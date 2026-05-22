from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsAdminUser
from .models import Department
from .serializers import DepartmentSerializer

class DepartmentViewSet(viewsets.ModelViewSet):
    """
    CRUD Viewset for hospital departments.
    Automatically scopes all reads and writes to the hospital linked to the request.
    """
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Enforce multi-tenant hospital scoping
        hospital = self.request.hospital
        if not hospital:
            return Department.objects.none()
        return Department.objects.filter(hospital=hospital).order_by('name')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return super().get_permissions()

    def perform_create(self, serializer):
        # Automatically assign the request hospital
        serializer.save(hospital=self.request.hospital)
