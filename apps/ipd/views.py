"""
IPD Views — Admission management and nurse vitals recording
"""
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from utils.permissions import IsAdminUser, IsNurseUser
from .models import IPDAdmission, VitalRecord
from .serializers import (
    IPDAdmissionListSerializer,
    IPDAdmissionDetailSerializer,
    IPDAdmissionCreateSerializer,
    VitalRecordSerializer
)

class IPDAdmissionViewSet(viewsets.ModelViewSet):
    """
    CRUD for IPD Admissions — scoped to request.hospital.
    Accessible by hospital-admin, frontdesk, nurse, and doctor.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return IPDAdmissionCreateSerializer
        if self.action == 'retrieve':
            return IPDAdmissionDetailSerializer
        return IPDAdmissionListSerializer

    def get_queryset(self):
        hospital = self.request.hospital
        qs = IPDAdmission.objects.select_related(
            'patient', 'attending_doctor', 'bed', 'bed__room'
        ).all()
        if hospital:
            qs = qs.filter(patient__user__hospital=hospital)

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs

    @transaction.atomic
    def perform_create(self, serializer):
        admission = serializer.save()
        # Mark bed as occupied on admission
        if admission.bed:
            admission.bed.status = 'occupied'
            admission.bed.save()

    @transaction.atomic
    def perform_update(self, serializer):
        old_bed = self.get_object().bed
        admission = serializer.save()
        # Free old bed if bed changed or patient discharged
        if admission.status == 'discharged' and admission.bed:
            admission.bed.status = 'available'
            admission.bed.save()
        elif old_bed and old_bed != admission.bed:
            old_bed.status = 'available'
            old_bed.save()
            if admission.bed:
                admission.bed.status = 'occupied'
                admission.bed.save()


class VitalRecordViewSet(viewsets.ModelViewSet):
    """
    CRUD for Vital Records — nurses record vitals per admission.
    """
    serializer_class = VitalRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        hospital = self.request.hospital
        qs = VitalRecord.objects.select_related('admission__patient').all()
        if hospital:
            qs = qs.filter(admission__patient__user__hospital=hospital)

        admission_id = self.request.query_params.get('admission')
        if admission_id:
            qs = qs.filter(admission_id=admission_id)

        return qs
