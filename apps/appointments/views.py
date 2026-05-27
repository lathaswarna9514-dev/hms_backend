"""
Appointment Views
"""
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from utils.permissions import IsAdminUser, IsPatientUser, IsFrontDesk
from .models import Appointment
from .serializers import (
    AppointmentListSerializer, AppointmentCreateSerializer,
    AppointmentPatientSerializer
)
from .services import AppointmentService
from utils.pagination import paginate_queryset_response


class AppointmentListView(APIView):
    """
    GET /api/appointments/  - Admin & Frontdesk: list appointments with filters
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not (user.is_admin or user.is_frontdesk):
            return Response({'success': False, 'message': 'Permission denied.'}, status=403)

        qs = Appointment.objects.select_related(
            'patient', 'schedule', 'schedule__doctor'
        ).all()

        # Hospital scoping for non-super-admin
        hospital = request.hospital
        if hospital:
            qs = qs.filter(schedule__doctor__user__hospital=hospital)

        search = request.query_params.get('search')
        date = request.query_params.get('date')
        doctor_id = request.query_params.get('doctor')
        upcoming = request.query_params.get('upcoming')
        appointment_type = request.query_params.get('appointment_type')
        department_type = request.query_params.get('department_type')

        if search:
            qs = qs.filter(
                Q(patient__name__icontains=search) |
                Q(patient__email__icontains=search) |
                Q(schedule__doctor__name__icontains=search) |
                Q(schedule__title__icontains=search)
            )
        if date:
            qs = qs.filter(schedule__schedule_date=date)
        if doctor_id:
            qs = qs.filter(schedule__doctor_id=doctor_id)
        if upcoming:
            qs = qs.filter(schedule__schedule_date__gte=timezone.now().date())
        if appointment_type:
            qs = qs.filter(appointment_type=appointment_type.upper())
        if department_type:
            qs = qs.filter(department_type=department_type.upper())

        return paginate_queryset_response(qs, request, AppointmentListSerializer)


class AppointmentDetailView(APIView):
    """
    DELETE /api/appointments/<id>/    - Admin or patient (own): cancel appointment
    """
    permission_classes = [IsAuthenticated]

    def _get_appointment(self, pk):
        try:
            return Appointment.objects.select_related('patient__user', 'schedule').get(pk=pk)
        except Appointment.DoesNotExist:
            return None

    def delete(self, request, pk):
        appointment = self._get_appointment(pk)
        if not appointment:
            return Response({'success': False, 'message': 'Appointment not found.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        # Admin can delete any; patient can only delete their own
        if not user.is_admin:
            if not (user.is_patient and
                    hasattr(user, 'patient_profile') and
                    appointment.patient == user.patient_profile):
                return Response({'success': False, 'message': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        AppointmentService.cancel_appointment(appointment)
        return Response({'success': True, 'message': 'Appointment cancelled.'})


class BookAppointmentView(APIView):
    """
    POST /api/appointments/book/
    Patient books a session. Assigns appointment number automatically.
    """
    permission_classes = [IsAuthenticated, IsPatientUser]

    def post(self, request):
        serializer = AppointmentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            patient = request.user.patient_profile
        except Exception:
            return Response({'success': False, 'message': 'Patient profile not found.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            appointment = AppointmentService.book_appointment(
                patient=patient,
                schedule_id=serializer.validated_data['schedule_id']
            )
        except ValueError as e:
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'message': f'Booking confirmed! Your appointment number is #{appointment.appointment_number}.',
            'data': {
                'appointment_number': appointment.appointment_number,
                'schedule_title': appointment.schedule.title,
                'doctor_name': appointment.schedule.doctor.name,
                'schedule_date': appointment.schedule.schedule_date,
                'schedule_time': appointment.schedule.schedule_time,
            }
        }, status=status.HTTP_201_CREATED)


class MyAppointmentsView(APIView):
    """
    GET /api/appointments/my/
    Patient: view own booking history.
    """
    permission_classes = [IsAuthenticated, IsPatientUser]

    def get(self, request):
        try:
            patient = request.user.patient_profile
        except Exception:
            return Response({'success': False, 'message': 'Patient profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        qs = Appointment.objects.filter(patient=patient).select_related(
            'schedule', 'schedule__doctor', 'schedule__doctor__specialty'
        ).order_by('-schedule__schedule_date')

        return paginate_queryset_response(qs, request, AppointmentPatientSerializer)


class DoctorAppointmentsView(APIView):
    """
    GET /api/appointments/doctor/
    Doctor: view appointments for their sessions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_doctor:
            return Response({'success': False, 'message': 'Only doctors can access this.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            doctor = request.user.doctor_profile
        except Exception:
            return Response({'success': False, 'message': 'Doctor profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        qs = Appointment.objects.filter(
            schedule__doctor=doctor
        ).select_related('patient', 'schedule').order_by('-schedule__schedule_date')

        return paginate_queryset_response(qs, request, AppointmentListSerializer)


class FrontDeskBookView(APIView):
    """
    POST /api/appointments/offline-book/
    Frontdesk books an appointment on behalf of a patient (offline/walk-in).
    Payload: { patient_id, schedule_id }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not (user.is_admin or user.is_frontdesk):
            return Response({'success': False, 'message': 'Permission denied.'}, status=403)

        patient_id = request.data.get('patient_id')
        schedule_id = request.data.get('schedule_id')

        if not patient_id or not schedule_id:
            return Response(
                {'success': False, 'message': 'patient_id and schedule_id are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from patients.models import Patient
        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return Response({'success': False, 'message': 'Patient not found.'}, status=404)

        try:
            appointment = AppointmentService.book_appointment(
                patient=patient,
                schedule_id=schedule_id
            )
        except ValueError as e:
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'message': f'Walk-in booking confirmed! Appointment #{appointment.appointment_number}.',
            'data': {
                'appointment_number': appointment.appointment_number,
                'patient_name': patient.name,
                'schedule_title': appointment.schedule.title,
                'doctor_name': appointment.schedule.doctor.name,
                'schedule_date': str(appointment.schedule.schedule_date),
                'schedule_time': str(appointment.schedule.schedule_time),
            }
        }, status=status.HTTP_201_CREATED)
