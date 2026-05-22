"""
Patient Views
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from utils.permissions import IsAdminUser, IsPatientUser
from .models import Patient
from .serializers import PatientListSerializer, PatientDetailSerializer, PatientUpdateSerializer


class PatientListView(APIView):
    """
    GET /api/patients/  - Admin & Frontdesk: list/search patients
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not (user.is_admin or user.is_frontdesk or user.is_doctor):
            return Response({'success': False, 'message': 'Permission denied.'}, status=403)

        search = request.query_params.get('search', '')
        hospital = request.hospital

        patients = Patient.objects.all()
        if hospital:
            patients = patients.filter(user__hospital=hospital)
        if search:
            from django.db.models import Q
            patients = patients.filter(
                Q(name__icontains=search) | Q(email__icontains=search) | Q(nic__icontains=search)
            )
        serializer = PatientListSerializer(patients, many=True)
        return Response({'success': True, 'count': patients.count(), 'data': serializer.data})


class PatientDetailView(APIView):
    """
    GET /api/patients/<id>/       - Admin or own patient view details
    DELETE /api/patients/<id>/    - Admin: delete patient
    """
    permission_classes = [IsAuthenticated]

    def _get_patient(self, pk):
        try:
            return Patient.objects.select_related('user').get(pk=pk)
        except Patient.DoesNotExist:
            return None

    def get(self, request, pk):
        patient = self._get_patient(pk)
        if not patient:
            return Response({'success': False, 'message': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Allow admin, doctor or the patient themselves
        user = request.user
        if not (user.is_admin or user.is_doctor or (user.is_patient and hasattr(user, 'patient_profile') and user.patient_profile.id == pk)):
            return Response({'success': False, 'message': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = PatientDetailSerializer(patient)
        return Response({'success': True, 'data': serializer.data})

    def delete(self, request, pk):
        if not request.user.is_admin:
            return Response({'success': False, 'message': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        patient = self._get_patient(pk)
        if not patient:
            return Response({'success': False, 'message': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            if patient.user:
                patient.user.delete()
            else:
                patient.delete()

        return Response({'success': True, 'message': 'Patient account deleted.'})


class PatientProfileView(APIView):
    """
    GET /api/patients/me/          - Patient: get own profile
    PUT /api/patients/me/          - Patient: update own profile/settings
    DELETE /api/patients/me/       - Patient: delete own account
    """
    permission_classes = [IsAuthenticated, IsPatientUser]

    def _get_my_patient(self, request):
        try:
            return request.user.patient_profile
        except Exception:
            return None

    def get(self, request):
        patient = self._get_my_patient(request)
        if not patient:
            return Response({'success': False, 'message': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PatientDetailSerializer(patient)
        return Response({'success': True, 'data': serializer.data})

    def put(self, request):
        patient = self._get_my_patient(request)
        if not patient:
            return Response({'success': False, 'message': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PatientUpdateSerializer(patient, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            password = serializer.validated_data.pop('password', None)
            serializer.validated_data.pop('confirm_password', None)
            for field, value in serializer.validated_data.items():
                setattr(patient, field, value)
            patient.save()
            if password:
                request.user.set_password(password)
                request.user.save()

        return Response({'success': True, 'message': 'Profile updated.', 'data': PatientDetailSerializer(patient).data})

    def delete(self, request):
        patient = self._get_my_patient(request)
        if not patient:
            return Response({'success': False, 'message': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            request.user.delete()  # Cascades to delete patient profile

        return Response({'success': True, 'message': 'Account deleted successfully.'})


class PatientHistoryView(APIView):
    """
    GET /api/patients/me/history/
    Retrieve inpatient stays, vitals, lab reports, and pharmacy history for the logged-in patient.
    """
    permission_classes = [IsAuthenticated, IsPatientUser]

    def get(self, request):
        try:
            patient = request.user.patient_profile
        except Exception:
            return Response({'success': False, 'message': 'Patient profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        # 1. IPD Admissions & Vitals
        from ipd.models import IPDAdmission
        from ipd.serializers import IPDAdmissionDetailSerializer
        admissions = IPDAdmission.objects.filter(patient=patient).prefetch_related('vitals')
        admissions_data = IPDAdmissionDetailSerializer(admissions, many=True).data

        # 2. Lab Reports (matching by patient name case-insensitively)
        from lab.models import LabRequest
        from lab.serializers import LabRequestSerializer
        lab_requests = LabRequest.objects.filter(patient_name__iexact=patient.name).order_by('-requested_at')
        lab_data = LabRequestSerializer(lab_requests, many=True).data

        # 3. Pharmacy Dispense Logs (matching by patient name case-insensitively)
        from pharmacy.models import DispenseOrder
        from pharmacy.serializers import DispenseOrderSerializer
        dispenses = DispenseOrder.objects.filter(patient_name__iexact=patient.name).order_by('-created_at')
        dispense_data = DispenseOrderSerializer(dispenses, many=True).data

        # 4. Prescriptions
        from opd.models import Prescription
        from opd.serializers import PrescriptionSerializer
        prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')
        prescriptions_data = PrescriptionSerializer(prescriptions, many=True).data

        return Response({
            'success': True,
            'data': {
                'ipd_admissions': admissions_data,
                'lab_requests': lab_data,
                'dispenses': dispense_data,
                'prescriptions': prescriptions_data
            }
        })


class PatientHistoryDetailView(APIView):
    """
    GET /api/patients/<id>/history/
    Retrieve inpatient stays, vitals, lab reports, pharmacy history, and prescriptions for a specific patient.
    Accessible by Admin, Doctor, or the patient themselves.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            patient = Patient.objects.get(pk=pk)
        except Patient.DoesNotExist:
            return Response({'success': False, 'message': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        is_own_profile = user.is_patient and hasattr(user, 'patient_profile') and user.patient_profile.id == pk
        if not (user.is_admin or user.is_doctor or is_own_profile):
            return Response({'success': False, 'message': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        # 1. IPD Admissions & Vitals
        from ipd.models import IPDAdmission
        from ipd.serializers import IPDAdmissionDetailSerializer
        admissions = IPDAdmission.objects.filter(patient=patient).prefetch_related('vitals')
        admissions_data = IPDAdmissionDetailSerializer(admissions, many=True).data

        # 2. Lab Requests
        from lab.models import LabRequest
        from lab.serializers import LabRequestSerializer
        lab_requests = LabRequest.objects.filter(patient_name__iexact=patient.name).order_by('-requested_at')
        lab_data = LabRequestSerializer(lab_requests, many=True).data

        # 3. Pharmacy Dispense Logs
        from pharmacy.models import DispenseOrder
        from pharmacy.serializers import DispenseOrderSerializer
        dispenses = DispenseOrder.objects.filter(patient_name__iexact=patient.name).order_by('-created_at')
        dispense_data = DispenseOrderSerializer(dispenses, many=True).data

        # 4. Prescriptions
        from opd.models import Prescription
        from opd.serializers import PrescriptionSerializer
        prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')
        prescriptions_data = PrescriptionSerializer(prescriptions, many=True).data

        return Response({
            'success': True,
            'data': {
                'ipd_admissions': admissions_data,
                'lab_requests': lab_data,
                'dispenses': dispense_data,
                'prescriptions': prescriptions_data
            }
        })
