"""
Dashboard Views
Admin and role-specific dashboard stats
"""
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from utils.permissions import IsAdminUser, IsSuperAdmin
from doctors.models import Doctor
from patients.models import Patient
from appointments.models import Appointment
from schedules.models import Schedule


class AdminDashboardView(APIView):
    """
    GET /api/dashboard/admin/
    Returns summary stats + upcoming appointments + upcoming sessions.
    Mirrors the PHP admin/index.php logic.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        today = timezone.now().date()
        next_week = today + timedelta(days=7)
        hospital = request.hospital

        # Scope filters
        doctor_qs = Doctor.objects.all()
        patient_qs = Patient.objects.all()
        appt_qs = Appointment.objects.all()
        schedule_qs = Schedule.objects.all()

        if hospital:
            doctor_qs = doctor_qs.filter(user__hospital=hospital)
            patient_qs = patient_qs.filter(user__hospital=hospital)
            appt_qs = appt_qs.filter(schedule__doctor__user__hospital=hospital)
            schedule_qs = schedule_qs.filter(doctor__user__hospital=hospital)

        # Summary counts
        doctor_count = doctor_qs.count()
        patient_count = patient_qs.count()
        upcoming_appointments = appt_qs.filter(
            schedule__schedule_date__gte=today
        ).count()
        today_sessions = schedule_qs.filter(schedule_date=today).count()

        # Upcoming appointments (next 7 days)
        recent_appointments = appt_qs.filter(
            schedule__schedule_date__gte=today,
            schedule__schedule_date__lte=next_week
        ).select_related('patient', 'schedule', 'schedule__doctor').order_by(
            'schedule__schedule_date'
        )[:20]

        appt_data = [
            {
                'appointment_number': a.appointment_number,
                'patient_name': a.patient.name,
                'doctor_name': a.schedule.doctor.name,
                'session_title': a.schedule.title,
                'schedule_date': a.schedule.schedule_date,
            }
            for a in recent_appointments
        ]

        # Upcoming sessions (next 7 days)
        upcoming_sessions = schedule_qs.filter(
            schedule_date__gte=today,
            schedule_date__lte=next_week
        ).select_related('doctor').order_by('schedule_date')[:20]

        session_data = [
            {
                'id': s.id,
                'title': s.title,
                'doctor_name': s.doctor.name,
                'schedule_date': s.schedule_date,
                'schedule_time': s.schedule_time,
                'booked_count': s.booked_count,
                'max_patients': s.max_patients,
            }
            for s in upcoming_sessions
        ]

        return Response({
            'success': True,
            'data': {
                'stats': {
                    'total_doctors': doctor_count,
                    'total_patients': patient_count,
                    'upcoming_appointments': upcoming_appointments,
                    'today_sessions': today_sessions,
                },
                'upcoming_appointments': appt_data,
                'upcoming_sessions': session_data,
                'today': str(today),
                'next_week_day': today + timedelta(days=7),
            }
        })


class PatientDashboardView(APIView):
    """
    GET /api/dashboard/patient/
    Returns patient's upcoming appointments and available sessions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_patient:
            from rest_framework import status
            return Response({'success': False, 'message': 'Access denied.'}, status=403)

        try:
            patient = request.user.patient_profile
        except Exception:
            from rest_framework import status
            return Response({'success': False, 'message': 'Patient profile not found.'}, status=404)

        today = timezone.now().date()

        # My upcoming appointments
        my_appointments = Appointment.objects.filter(
            patient=patient,
            schedule__schedule_date__gte=today
        ).select_related('schedule', 'schedule__doctor').order_by('schedule__schedule_date')[:10]

        appt_data = [
            {
                'appointment_number': a.appointment_number,
                'session_title': a.schedule.title,
                'doctor_name': a.schedule.doctor.name,
                'schedule_date': a.schedule.schedule_date,
                'schedule_time': a.schedule.schedule_time,
            }
            for a in my_appointments
        ]

        return Response({
            'success': True,
            'data': {
                'patient_name': patient.name,
                'upcoming_appointments': appt_data,
                'total_bookings': Appointment.objects.filter(patient=patient).count(),
                'today': str(today),
            }
        })


class DoctorDashboardView(APIView):
    """
    GET /api/dashboard/doctor/
    Returns doctor's upcoming sessions and patient counts.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_doctor:
            return Response({'success': False, 'message': 'Access denied.'}, status=403)

        try:
            doctor = request.user.doctor_profile
        except Exception:
            return Response({'success': False, 'message': 'Doctor profile not found.'}, status=404)

        today = timezone.now().date()

        upcoming_sessions = Schedule.objects.filter(
            doctor=doctor,
            schedule_date__gte=today
        ).order_by('schedule_date')[:10]

        session_data = [
            {
                'id': s.id,
                'title': s.title,
                'schedule_date': s.schedule_date,
                'schedule_time': s.schedule_time,
                'booked_count': s.booked_count,
                'max_patients': s.max_patients,
            }
            for s in upcoming_sessions
        ]

        return Response({
            'success': True,
            'data': {
                'doctor_name': doctor.name,
                'specialty': doctor.specialty.name if doctor.specialty else '',
                'upcoming_sessions': session_data,
                'total_sessions': Schedule.objects.filter(doctor=doctor).count(),
                'today': str(today),
            }
        })


class SuperAdminDashboardView(APIView):
    """
    GET /api/dashboard/super-admin/
    Returns global system metrics for the platform super admin dashboard.
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        from hospitals.models import Hospital
        from support.models import SupportTicket

        hospitals_count = Hospital.objects.count()
        patients_count = Patient.objects.count()
        doctors_count = Doctor.objects.count()
        tickets_count = SupportTicket.objects.filter(status='open').count()

        # Fetch recent hospitals provisioned
        recent_hospitals = Hospital.objects.all().order_by('-created_at')[:5]
        hospitals_data = [
            {
                'id': h.id,
                'name': h.name,
                'email': h.email,
                'phone': h.phone,
                'is_active': h.is_active,
                'created_at': h.created_at
            }
            for h in recent_hospitals
        ]

        # Fetch recent tickets
        recent_tickets = SupportTicket.objects.all().order_by('-created_at')[:5]
        tickets_data = [
            {
                'id': t.id,
                'subject': t.subject,
                'name': t.name,
                'email': t.email,
                'status': t.status,
                'created_at': t.created_at
            }
            for t in recent_tickets
        ]

        return Response({
            'success': True,
            'data': {
                'stats': {
                    'total_hospitals': hospitals_count,
                    'total_patients': patients_count,
                    'total_doctors': doctors_count,
                    'pending_tickets': tickets_count
                },
                'recent_hospitals': hospitals_data,
                'recent_tickets': tickets_data
            }
        })


class HospitalAdminAnalyticsView(APIView):
    """
    GET /api/dashboard/admin/analytics/
    Returns analytics metrics and graph datasets for hospital dashboards.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hospital = request.hospital
        if not hospital:
            return Response({
                'success': False, 
                'message': 'This endpoint is only available for scoped Hospital Administrators.'
            }, status=400)

        # 1. OPD Census Queues (Past 7 days throughput)
        today = timezone.now().date()
        past_week = [today - timedelta(days=i) for i in range(6, -1, -1)]
        census_labels = [day.strftime('%a %d %b') for day in past_week]
        census_data = []

        from appointments.models import Appointment
        for day in past_week:
            count = Appointment.objects.filter(
                schedule__doctor__user__hospital=hospital,
                schedule__schedule_date=day
            ).count()
            census_data.append(count)

        # 2. Revenue collections per month (past 6 months)
        from billing.models import Invoice
        monthly_revenue_labels = []
        monthly_revenue_data = []
        for i in range(5, -1, -1):
            start_of_month = (timezone.now() - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0)
            next_month = (start_of_month + timedelta(days=32)).replace(day=1)
            
            settled_invoices = Invoice.objects.filter(
                hospital=hospital,
                status='paid',
                created_at__gte=start_of_month,
                created_at__lt=next_month
            )
            total = sum([float(inv.total_amount) for inv in settled_invoices])
            monthly_revenue_labels.append(start_of_month.strftime('%b %Y'))
            monthly_revenue_data.append(total)

        # 3. Pharmacy Batch Inventory stock quantities
        from pharmacy.models import Medicine
        medicines = Medicine.objects.filter(hospital=hospital).order_by('stock_quantity')[:10]
        med_labels = [med.name for med in medicines]
        med_stock = [med.stock_quantity for med in medicines]

        # 4. Lab Test Volumes (Popular Profiles)
        from lab.models import LabRequest
        from django.db.models import Count
        popular_tests = LabRequest.objects.filter(hospital=hospital)\
            .values('test__name')\
            .annotate(count=Count('id'))\
            .order_by('-count')[:5]
        
        lab_labels = [pt['test__name'] for pt in popular_tests]
        lab_counts = [pt['count'] for pt in popular_tests]

        return Response({
            'success': True,
            'data': {
                'census': {
                    'labels': census_labels,
                    'data': census_data
                },
                'revenue': {
                    'labels': monthly_revenue_labels,
                    'data': monthly_revenue_data
                },
                'pharmacy': {
                    'labels': med_labels,
                    'data': med_stock
                },
                'lab': {
                    'labels': lab_labels,
                    'data': lab_counts
                }
            }
        })


class SuperAdminAnalyticsView(APIView):
    """
    GET /api/dashboard/super-admin/analytics/
    Returns analytics metrics and graph datasets for the super admin platform.
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        from hospitals.models import Hospital
        from patients.models import Patient
        from doctors.models import Doctor

        # Mock data for platform growth (past 6 months)
        today = timezone.now().date()
        months = []
        hospitals_data = []
        patients_data = []

        for i in range(5, -1, -1):
            start_date = (timezone.now() - timedelta(days=30 * i)).replace(day=1)
            months.append(start_date.strftime('%b %Y'))
            # Mock historical count logic
            hospitals_data.append(Hospital.objects.filter(created_at__lte=start_date + timedelta(days=31)).count())
            patients_data.append(Patient.objects.filter(created_at__lte=start_date + timedelta(days=31)).count())

        return Response({
            'success': True,
            'data': {
                'growth': {
                    'labels': months,
                    'hospitals': hospitals_data,
                    'patients': patients_data
                }
            }
        })
