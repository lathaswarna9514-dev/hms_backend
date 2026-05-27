"""
Doctor Views
DRF ViewSets for doctor management (admin only CRUD + public list)
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from utils.permissions import IsAdminUser
from utils.pagination import paginate_queryset_response
from .models import Doctor, Specialty
from .serializers import (
    DoctorListSerializer, DoctorDetailSerializer,
    DoctorCreateSerializer, DoctorUpdateSerializer,
    SpecialtySerializer
)
from .services import DoctorService


class SpecialtyListView(APIView):
    """
    GET /api/doctors/specialties/
    Returns all medical specialties. Public endpoint.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        specialties = Specialty.objects.all().order_by('name')
        serializer = SpecialtySerializer(specialties, many=True)
        return Response({'success': True, 'data': serializer.data})


class DoctorListView(APIView):
    """
    GET /api/doctors/                  - List all doctors (public/scoped)
    POST /api/doctors/                 - Create doctor (admin only)
    """
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]

    def get(self, request):
        search = request.query_params.get('search', '')
        hospital = request.hospital
        
        doctors = Doctor.objects.select_related('specialty').all()
        if hospital:
            doctors = doctors.filter(user__hospital=hospital)
            
        if search:
            from django.db.models import Q
            doctors = doctors.filter(
                Q(name__icontains=search) | Q(email__icontains=search)
            )
        return paginate_queryset_response(doctors, request, DoctorListSerializer)

    def post(self, request):
        serializer = DoctorCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        doctor = DoctorService.create_doctor(serializer.validated_data, request.hospital)
        return Response(
            {'success': True, 'message': 'Doctor added successfully.', 'data': DoctorDetailSerializer(doctor).data},
            status=status.HTTP_201_CREATED
        )


class DoctorDetailView(APIView):
    """
    GET /api/doctors/<id>/             - View doctor details
    PUT /api/doctors/<id>/             - Update doctor (admin only)
    DELETE /api/doctors/<id>/          - Delete doctor (admin only)
    """
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        if self.request.method == 'PUT':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def _get_doctor(self, pk):
        try:
            qs = Doctor.objects.select_related('specialty', 'user')
            if self.request.hospital:
                qs = qs.filter(user__hospital=self.request.hospital)
            return qs.get(pk=pk)
        except Doctor.DoesNotExist:
            return None

    def get(self, request, pk):
        doctor = self._get_doctor(pk)
        if not doctor:
            return Response({'success': False, 'message': 'Doctor not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = DoctorDetailSerializer(doctor)
        return Response({'success': True, 'data': serializer.data})

    def put(self, request, pk):
        doctor = self._get_doctor(pk)
        if not doctor:
            return Response({'success': False, 'message': 'Doctor not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions: user must be super-admin, hospital-admin, or the doctor themselves
        is_admin = request.user.usertype in ('super-admin', 'hospital-admin')
        is_self = (doctor.user == request.user)
        if not (is_admin or is_self):
            return Response({'success': False, 'message': 'Administrator access required.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = DoctorUpdateSerializer(doctor, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        updated = DoctorService.update_doctor(doctor, serializer.validated_data)
        return Response({'success': True, 'message': 'Doctor updated successfully.', 'data': DoctorDetailSerializer(updated).data})

    def delete(self, request, pk):
        doctor = self._get_doctor(pk)
        if not doctor:
            return Response({'success': False, 'message': 'Doctor not found.'}, status=status.HTTP_404_NOT_FOUND)
        DoctorService.delete_doctor(doctor)
        return Response({'success': True, 'message': 'Doctor removed successfully.'}, status=status.HTTP_200_OK)


from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import LeaveRequest
from .serializers import LeaveRequestSerializer

class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            hospital = self.request.hospital
            if not hospital:
                return LeaveRequest.objects.none()
            return LeaveRequest.objects.filter(doctor__user__hospital=hospital)
        elif user.is_doctor:
            try:
                doctor = user.doctor_profile
                return LeaveRequest.objects.filter(doctor=doctor)
            except Exception:
                return LeaveRequest.objects.none()
        else:
            return LeaveRequest.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_doctor:
            raise PermissionDenied("Only doctors can submit leave requests.")
        try:
            doctor = user.doctor_profile
        except Exception:
            raise ValidationError("Doctor profile not found.")
        serializer.save(doctor=doctor, status='PENDING')

    def perform_update(self, serializer):
        user = self.request.user
        if user.is_admin:
            serializer.save()
        elif user.is_doctor:
            instance = self.get_object()
            if instance.status != 'PENDING':
                raise PermissionDenied("Cannot modify an already processed leave request.")
            serializer.save(status='PENDING')
        else:
            raise PermissionDenied("Permission denied.")
