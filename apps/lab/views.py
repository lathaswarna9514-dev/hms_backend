"""
Lab Views — Handles lab catalog management and clinical testing requests
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import LabTest, LabRequest
from .serializers import (
    LabTestSerializer, LabRequestSerializer,
    LabRequestDetailSerializer, LabRequestCreateSerializer
)


class LabTestViewSet(viewsets.ModelViewSet):
    """
    CRUD for Lab test definitions — scoped to request.hospital.
    """
    serializer_class = LabTestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not (user.is_admin or user.is_lab or user.is_doctor):
            return LabTest.objects.none()

        hospital = self.request.hospital
        qs = LabTest.objects.all()
        if hospital:
            qs = qs.filter(hospital=hospital)
        
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(name__icontains=search)
            
        return qs

    def perform_create(self, serializer):
        serializer.save(hospital=self.request.hospital)


class LabRequestViewSet(viewsets.ModelViewSet):
    """
    Laboratory diagnostic request queue — sample tracking and reports release.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return LabRequestCreateSerializer
        if self.action == 'retrieve':
            return LabRequestDetailSerializer
        return LabRequestSerializer

    def get_queryset(self):
        user = self.request.user
        # Allow doctors, lab technicians and admins
        if not (user.is_admin or user.is_lab or user.is_doctor):
            return LabRequest.objects.none()

        hospital = self.request.hospital
        qs = LabRequest.objects.select_related('test').all()
        if hospital:
            qs = qs.filter(hospital=hospital)

        # Filters
        status_filter = self.request.query_params.get('status')
        search = self.request.query_params.get('search')
        
        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(patient_name__icontains=search)

        return qs

    def perform_create(self, serializer):
        serializer.save(hospital=self.request.hospital)

    @action(detail=True, methods=['post'], url_path='collect-sample')
    def collect_sample(self, request, pk=None):
        """POST /api/lab/requests/<id>/collect-sample/ — Log sample received."""
        req = self.get_object()
        barcode = request.data.get('sample_barcode', '')
        if not barcode:
            return Response({'success': False, 'message': 'Barcode is required.'}, status=400)

        req.sample_barcode = barcode
        req.status = 'collected'
        req.sample_collected_at = timezone.now()
        req.save()
        return Response({
            'success': True,
            'message': 'Sample logged successfully.',
            'status': req.status,
            'sample_collected_at': req.sample_collected_at
        })

    @action(detail=True, methods=['post'], url_path='submit-results')
    def submit_results(self, request, pk=None):
        """POST /api/lab/requests/<id>/submit-results/ — Write report outcomes."""
        req = self.get_object()
        result = request.data.get('test_result', '')
        notes = request.data.get('technician_notes', '')

        if not result:
            return Response({'success': False, 'message': 'Test result metrics are required.'}, status=400)

        req.test_result = result
        req.technician_notes = notes
        req.status = 'completed'
        req.completed_at = timezone.now()
        req.save()
        return Response({
            'success': True,
            'message': 'Lab results released successfully.',
            'status': req.status,
            'completed_at': req.completed_at
        })
