from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsSuperAdmin, IsAdminUser
from .models import Hospital
from .serializers import HospitalSerializer


class HospitalViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoint for Hospital models.
    Permits anyone to read hospital lists, but restricts creation and modifications to Super Admins.
    """
    queryset = Hospital.objects.all().order_by('-created_at')
    serializer_class = HospitalSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]


class HospitalSelfView(APIView):
    """
    GET  /api/hospitals/me/  — Return the current admin's scoped hospital.
    PATCH /api/hospitals/me/ — Partially update their own hospital details.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        hospital = request.hospital
        if not hospital:
            return Response({'success': False, 'message': 'No hospital linked to this account.'}, status=404)
        serializer = HospitalSerializer(hospital)
        return Response({'success': True, 'data': serializer.data})

    def patch(self, request):
        hospital = request.hospital
        if not hospital:
            return Response({'success': False, 'message': 'No hospital linked to this account.'}, status=404)
        serializer = HospitalSerializer(hospital, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({'success': True, 'message': 'Hospital settings updated.', 'data': serializer.data})
