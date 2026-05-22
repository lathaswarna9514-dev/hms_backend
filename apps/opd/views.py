from rest_framework import viewsets, permissions
from .models import Prescription
from .serializers import PrescriptionSerializer, PrescriptionCreateSerializer

class PrescriptionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PrescriptionCreateSerializer
        return PrescriptionSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Prescription.objects.select_related('patient', 'doctor').all()

        # Scoping based on user role
        if user.usertype == 'patient' and hasattr(user, 'patient_profile'):
            qs = qs.filter(patient=user.patient_profile)

        # Filters
        patient_id = self.request.query_params.get('patient')
        doctor_id = self.request.query_params.get('doctor')
        
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if doctor_id:
            qs = qs.filter(doctor_id=doctor_id)

        return qs
