from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsAdminUser
from .models import Room, Bed
from .serializers import RoomSerializer, BedSerializer

class RoomViewSet(viewsets.ModelViewSet):
    """
    CRUD Viewset for hospital Rooms.
    Scopes queries to the hospital linked to the request.
    """
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        hospital = self.request.hospital
        if not hospital:
            return Room.objects.none()
        return Room.objects.filter(hospital=hospital).order_by('room_number')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(hospital=self.request.hospital)


class BedViewSet(viewsets.ModelViewSet):
    """
    CRUD Viewset for hospital Beds.
    Scopes queries to rooms linked to the hospital in the request.
    """
    serializer_class = BedSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        hospital = self.request.hospital
        if not hospital:
            return Bed.objects.none()
        return Bed.objects.filter(room__hospital=hospital).order_by('room__room_number', 'bed_number')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return super().get_permissions()
