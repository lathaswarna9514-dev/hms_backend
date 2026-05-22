from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Attendance
from .serializers import AttendanceSerializer
from authentication.models import WebUser
from utils.permissions import IsAdminUser

class SystemStatusView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return Response({'success': True, 'status': 'operational'})

class AttendanceViewSet(viewsets.ModelViewSet):
    """
    CRUD Endpoint for managing Attendance.
    Hospital Admins can view and manage attendance for their hospital's staff.
    Staff members can view their own attendance.
    """
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            hospital = self.request.hospital
            if not hospital:
                return Attendance.objects.none()
            return Attendance.objects.filter(user__hospital=hospital, user__usertype='doctor')
        return Attendance.objects.filter(user=user, user__usertype='doctor')

    def create(self, request, *args, **kwargs):
        # Allow admin to create for staff, or staff to create for themselves
        user_id = request.data.get('user')
        if not user_id:
            user_id = request.user.id
        
        try:
            target_user = WebUser.objects.get(id=user_id)
        except WebUser.DoesNotExist:
            return Response({'success': False, 'message': 'User not found.'}, status=404)

        if target_user.usertype != 'doctor':
            return Response({'success': False, 'message': 'Attendance tracking is restricted to doctor profiles.'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.is_admin:
            if target_user.hospital != request.hospital:
                return Response({'success': False, 'message': 'User not in your hospital.'}, status=403)
        else:
            if target_user.id != request.user.id:
                return Response({'success': False, 'message': 'Cannot mark attendance for another user.'}, status=403)

        # Check if attendance already exists for today
        date = request.data.get('date')
        if not date:
            from django.utils import timezone
            date = timezone.now().date()
            
        if Attendance.objects.filter(user=target_user, date=date).exists():
            return Response({'success': False, 'message': 'Attendance already marked for this date.'}, status=400)

        data = request.data.copy()
        data['user'] = target_user.id
        if 'date' not in data:
            data['date'] = date

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsSuperAdmin

class AuditLogView(APIView):
    """
    GET /api/common/audit-logs/
    Returns system audit logs.
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        return Response({
            'success': True,
            'data': [
                {'id': 1, 'action': 'Login', 'user': 'Admin 1', 'timestamp': '2023-10-01T10:00:00Z'},
                {'id': 2, 'action': 'Update Settings', 'user': 'Admin 1', 'timestamp': '2023-10-01T11:00:00Z'},
            ]
        })

class BroadcastMessageView(APIView):
    """
    GET /api/common/broadcast/
    POST /api/common/broadcast/
    Manage system broadcast messages.
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        return Response({
            'success': True,
            'data': [
                {'id': 1, 'message': 'System maintenance at midnight', 'status': 'sent'},
            ]
        })
    
    def post(self, request):
        return Response({'success': True, 'message': 'Broadcast message sent.'})

class ContentManagementView(APIView):
    """
    GET /api/common/cms/
    Manage CMS content for the landing pages.
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        return Response({
            'success': True,
            'data': [
                {'id': 1, 'section': 'Hero Banner', 'content': 'Welcome to eDoc'},
            ]
        })

class QRCodeGeneratorView(APIView):
    """
    POST /api/common/qr-generate/
    Generate QR codes.
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        return Response({'success': True, 'qr_code_url': 'http://example.com/qr.png'})
