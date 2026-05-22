from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsAdminUser, IsPatientUser

from .models import Invoice, InvoiceItem
from .serializers import InvoiceSerializer, InvoiceItemSerializer
from patients.models import Patient
from ipd.models import IPDAdmission
from lab.models import LabRequest
from pharmacy.models import DispenseOrder

class InvoiceListView(APIView):
    """
    GET /api/billing/invoices/ - Frontdesk & Admin list invoices. Scoped by hospital.
    POST /api/billing/invoices/ - Create custom invoice.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not (user.is_admin or user.is_frontdesk):
            return Response({'success': False, 'message': 'Permission denied.'}, status=403)

        hospital = request.hospital
        qs = Invoice.objects.select_related('patient').prefetch_related('items').all()
        if hospital:
            qs = qs.filter(hospital=hospital)

        # Filters
        search = request.query_params.get('search')
        status_filter = request.query_params.get('status')
        billing_type = request.query_params.get('billing_type')

        if search:
            qs = qs.filter(
                Q(patient__name__icontains=search) |
                Q(patient__email__icontains=search)
            )
        if status_filter:
            qs = qs.filter(status=status_filter)
        if billing_type:
            qs = qs.filter(billing_type=billing_type)

        serializer = InvoiceSerializer(qs, many=True)
        return Response({'success': True, 'count': qs.count(), 'data': serializer.data})

    def post(self, request):
        user = request.user
        if not (user.is_admin or user.is_frontdesk):
            return Response({'success': False, 'message': 'Permission denied.'}, status=403)

        payload = request.data
        patient_id = payload.get('patient_id')
        items = payload.get('items', []) # Expected list of dicts: {name, quantity, unit_price}

        if not patient_id or not items:
            return Response({'success': False, 'message': 'Patient and invoice line items are required.'}, status=400)

        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return Response({'success': False, 'message': 'Patient not found.'}, status=404)

        hospital = request.hospital or patient.user.hospital
        if not hospital:
            return Response({'success': False, 'message': 'No hospital node configured.'}, status=400)

        try:
            with transaction.atomic():
                invoice = Invoice.objects.create(
                    hospital=hospital,
                    patient=patient,
                    billing_type=payload.get('billing_type', 'general'),
                    discount=float(payload.get('discount', 0)),
                    tax=float(payload.get('tax', 0)),
                    status='pending'
                )

                subtotal = 0.00
                for item in items:
                    unit_p = float(item.get('unit_price', 0))
                    qty = int(item.get('quantity', 1))
                    line_total = unit_p * qty
                    subtotal += line_total

                    InvoiceItem.objects.create(
                        invoice=invoice,
                        name=item.get('name'),
                        quantity=qty,
                        unit_price=unit_p
                    )

                invoice.subtotal = subtotal
                # total = subtotal - discount + tax
                invoice.total_amount = subtotal - float(invoice.discount) + float(invoice.tax)
                invoice.save()

            return Response({
                'success': True,
                'message': 'Invoice generated successfully.',
                'data': InvoiceSerializer(invoice).data
            }, status=201)

        except Exception as e:
            return Response({'success': False, 'message': str(e)}, status=400)


class InvoiceDetailView(APIView):
    """
    GET /api/billing/invoices/<id>/ - Details of invoice.
    POST /api/billing/invoices/<id>/pay/ - Mark invoice as paid.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            invoice = Invoice.objects.select_related('patient').prefetch_related('items').get(pk=pk)
        except Invoice.DoesNotExist:
            return Response({'success': False, 'message': 'Invoice not found.'}, status=404)

        user = request.user
        # Admin, frontdesk or the patient themselves
        if not (user.is_admin or user.is_frontdesk):
            if not (user.is_patient and hasattr(user, 'patient_profile') and invoice.patient == user.patient_profile):
                return Response({'success': False, 'message': 'Permission denied.'}, status=403)

        return Response({'success': True, 'data': InvoiceSerializer(invoice).data})

    def post(self, request, pk):
        # Pay endpoint
        user = request.user
        if not (user.is_admin or user.is_frontdesk):
            return Response({'success': False, 'message': 'Permission denied.'}, status=403)

        try:
            invoice = Invoice.objects.get(pk=pk)
        except Invoice.DoesNotExist:
            return Response({'success': False, 'message': 'Invoice not found.'}, status=404)

        if invoice.status == 'paid':
            return Response({'success': False, 'message': 'Invoice is already paid.'}, status=400)

        invoice.status = 'paid'
        invoice.save()
        return Response({'success': True, 'message': 'Payment logged successfully. Invoice is settled.', 'data': InvoiceSerializer(invoice).data})


class CompileIPDInvoiceView(APIView):
    """
    POST /api/billing/invoices/compile-ipd/
    Compiles all inpatient stay charges (bed nights, lab tests, pharmacy) for an admission.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not (user.is_admin or user.is_frontdesk):
            return Response({'success': False, 'message': 'Permission denied.'}, status=403)

        admission_id = request.data.get('admission_id')
        if not admission_id:
            return Response({'success': False, 'message': 'admission_id is required.'}, status=400)

        try:
            admission = IPDAdmission.objects.select_related('patient', 'bed__room', 'attending_doctor').get(pk=admission_id)
        except IPDAdmission.DoesNotExist:
            return Response({'success': False, 'message': 'IPD Admission stay record not found.'}, status=404)

        patient = admission.patient
        hospital = request.hospital or admission.patient.user.hospital

        # 1. Calculate Bed Nights Charge
        end_time = admission.discharge_date if admission.discharge_date else timezone.now()
        duration = end_time - admission.admission_date
        nights = max(1, duration.days)
        bed_charge_rate = float(admission.bed.room.charges_per_day) if (admission.bed and admission.bed.room) else 0.00
        bed_total = bed_charge_rate * nights

        # 2. Compile Lab tests ordered during inpatient stay matching patient's name
        labs = LabRequest.objects.select_related('test').filter(
            patient_name__iexact=patient.name,
            requested_at__gte=admission.admission_date
        )
        # Filter completed lab tests to charge
        labs_completed = labs.filter(status='completed')

        # 3. Compile Pharmacy medications dispensed during inpatient stay matching patient's name
        dispenses = DispenseOrder.objects.select_related('medicine').filter(
            patient_name__iexact=patient.name,
            created_at__gte=admission.admission_date
        )

        try:
            with transaction.atomic():
                # Check if an IPD invoice already exists for this admission to avoid duplicate compile
                existing = Invoice.objects.filter(patient=patient, billing_type='ipd', status='pending', created_at__gte=admission.admission_date).first()
                if existing:
                    return Response({
                        'success': False,
                        'message': 'A pending IPD invoice already exists for this admission.',
                        'data': InvoiceSerializer(existing).data
                    })

                invoice = Invoice.objects.create(
                    hospital=hospital,
                    patient=patient,
                    billing_type='ipd',
                    status='pending'
                )

                # Add Bed Charge Item
                room_label = admission.bed.room.room_number if (admission.bed and admission.bed.room) else 'N/A'
                InvoiceItem.objects.create(
                    invoice=invoice,
                    name=f"Inpatient Room/Bed stay: {nights} night(s) [Room {room_label}]",
                    quantity=nights,
                    unit_price=bed_charge_rate
                )

                subtotal = bed_total

                # Add Lab Test Items
                for l in labs_completed:
                    unit_cost = float(l.test.cost) if l.test else 0.0
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        name=f"Pathology Lab Test: {l.test.name} ({l.test.test_code})" if l.test else "Lab Test",
                        quantity=1,
                        unit_price=unit_cost
                    )
                    subtotal += unit_cost

                # Add Pharmacy Items
                for d in dispenses:
                    unit_cost = float(d.unit_price)
                    qty = int(d.quantity)
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        name=f"Medication Dispensed: {d.medicine.name}" if d.medicine else "Pharmacy Item",
                        quantity=qty,
                        unit_price=unit_cost
                    )
                    subtotal += (unit_cost * qty)

                # Update invoice totals
                invoice.subtotal = subtotal
                invoice.total_amount = subtotal
                invoice.save()

            return Response({
                'success': True,
                'message': 'IPD stay charges compiled successfully into pending invoice.',
                'data': InvoiceSerializer(invoice).data
            }, status=201)

        except Exception as e:
            return Response({'success': False, 'message': str(e)}, status=400)


class MyInvoicesView(APIView):
    """
    GET /api/billing/my-invoices/ - Patient retrieves own invoices.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user.is_patient:
            return Response({'success': False, 'message': 'Only patients can view their bills.'}, status=403)

        try:
            patient = user.patient_profile
        except Exception:
            return Response({'success': False, 'message': 'Patient profile not found.'}, status=404)

        invoices = Invoice.objects.filter(patient=patient).prefetch_related('items').order_by('-created_at')
        serializer = InvoiceSerializer(invoices, many=True)
        return Response({'success': True, 'count': invoices.count(), 'data': serializer.data})
