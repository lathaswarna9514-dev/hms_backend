"""
Schedule Views
"""
from django.utils import timezone
from django.db.models import Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from utils.permissions import IsAdminUser
from .models import Schedule
from .serializers import (
    ScheduleListSerializer, ScheduleDetailSerializer,
    ScheduleCreateSerializer, ScheduleBookingInfoSerializer
)
from utils.pagination import paginate_queryset_response


class ScheduleListView(APIView):
    """
    GET /api/schedules/    - List all sessions (public, filterable)
    POST /api/schedules/   - Create session (admin or doctor)
    """
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        from rest_framework.permissions import BasePermission
        class IsAdminOrDoctor(BasePermission):
            def has_permission(self, request, view):
                return bool(
                    request.user and
                    request.user.is_authenticated and
                    (request.user.usertype in ('super-admin', 'hospital-admin') or request.user.usertype == 'doctor')
                )
        return [IsAdminOrDoctor()]

    def get(self, request):
        qs = Schedule.objects.select_related('doctor', 'doctor__specialty').all()

        # Filters
        date = request.query_params.get('date')
        doctor_id = request.query_params.get('doctor')
        search = request.query_params.get('search')
        upcoming = request.query_params.get('upcoming')
        hospital_id = request.query_params.get('hospital') or request.query_params.get('hospital_id')

        if date:
            qs = qs.filter(schedule_date=date)
        if doctor_id:
            qs = qs.filter(doctor_id=doctor_id)
        if hospital_id:
            qs = qs.filter(doctor__user__hospital_id=hospital_id)
        elif request.hospital_id:
            qs = qs.filter(doctor__user__hospital_id=request.hospital_id)
            
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(doctor__name__icontains=search) |
                Q(schedule_date__icontains=search)
            )
        if upcoming:
            qs = qs.filter(schedule_date__gte=timezone.now().date())

        return paginate_queryset_response(qs, request, ScheduleListSerializer)

    def post(self, request):
        data = request.data.copy()
        if request.user.usertype == 'doctor':
            try:
                data['doctor'] = request.user.doctor_profile.id
            except Exception:
                return Response({'success': False, 'message': 'Doctor profile not found.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ScheduleCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        schedule = serializer.save()
        return Response(
            {'success': True, 'message': f'Session "{schedule.title}" scheduled.', 'data': ScheduleDetailSerializer(schedule).data},
            status=status.HTTP_201_CREATED
        )


class ScheduleDetailView(APIView):
    """
    GET /api/schedules/<id>/       - View session (includes booked patients for admin and owner doctor)
    DELETE /api/schedules/<id>/    - Delete session (admin or owner doctor)
    """
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def _get_schedule(self, pk):
        try:
            return Schedule.objects.select_related('doctor').get(pk=pk)
        except Schedule.DoesNotExist:
            return None

    def get(self, request, pk):
        schedule = self._get_schedule(pk)
        if not schedule:
            return Response({'success': False, 'message': 'Session not found.'}, status=status.HTTP_404_NOT_FOUND)

        data = ScheduleDetailSerializer(schedule).data

        # Admin sees full patient list; owner doctor sees full patient list; patient sees booking info
        is_owner_doctor = (
            request.user.is_authenticated and
            request.user.usertype == 'doctor' and
            hasattr(request.user, 'doctor_profile') and
            schedule.doctor == request.user.doctor_profile
        )
        if request.user.is_authenticated and (request.user.is_admin or is_owner_doctor):
            from appointments.serializers import AppointmentInScheduleSerializer
            appointments = schedule.appointments.select_related('patient').all()
            data['booked_patients'] = AppointmentInScheduleSerializer(appointments, many=True).data

        return Response({'success': True, 'data': data})

    def delete(self, request, pk):
        schedule = self._get_schedule(pk)
        if not schedule:
            return Response({'success': False, 'message': 'Session not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.usertype in ('super-admin', 'hospital-admin'):
            is_owner = (
                request.user.usertype == 'doctor' and
                hasattr(request.user, 'doctor_profile') and
                schedule.doctor == request.user.doctor_profile
            )
            if not is_owner:
                return Response({'success': False, 'message': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        title = schedule.title
        schedule.delete()
        return Response({'success': True, 'message': f'Session "{title}" removed.'})


class ScheduleBookingInfoView(APIView):
    """
    GET /api/schedules/<id>/booking-info/
    Returns session details for the patient booking confirmation page.
    Includes next appointment number.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            schedule = Schedule.objects.select_related('doctor').get(pk=pk)
        except Schedule.DoesNotExist:
            return Response({'success': False, 'message': 'Session not found.'}, status=status.HTTP_404_NOT_FOUND)

        if schedule.is_full:
            return Response({'success': False, 'message': 'This session is fully booked.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ScheduleBookingInfoSerializer(schedule)
        return Response({'success': True, 'data': serializer.data})


class MySchedulesView(APIView):
    """
    GET /api/schedules/my/
    Doctor: view own upcoming sessions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_doctor:
            return Response({'success': False, 'message': 'Only doctors can access this.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            doctor = request.user.doctor_profile
        except Exception:
            return Response({'success': False, 'message': 'Doctor profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        qs = Schedule.objects.filter(
            doctor=doctor,
            schedule_date__gte=timezone.now().date()
        ).order_by('schedule_date', 'schedule_time')

        return paginate_queryset_response(qs, request, ScheduleListSerializer)


from rest_framework import viewsets
from .models import Shift
from .serializers import ShiftSerializer

class ShiftViewSet(viewsets.ModelViewSet):
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        hospital = self.request.hospital
        if not hospital:
            return Shift.objects.none()
        return Shift.objects.filter(hospital=hospital)

    def perform_create(self, serializer):
        serializer.save(hospital=self.request.hospital)

