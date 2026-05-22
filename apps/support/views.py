from rest_framework import viewsets, permissions
from utils.permissions import IsSuperAdmin
from .models import SupportTicket
from .serializers import SupportTicketSerializer

class SupportTicketViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoint for Support Tickets.
    Permits anyone to create a ticket, limits viewing to own tickets for staff/patients,
    and grants full visibility to Super Admins.
    """
    serializer_class = SupportTicketSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if not user or user.is_anonymous:
            return SupportTicket.objects.none()
        
        # Super admin has unrestricted audit visibility
        if user.usertype == 'super-admin' or getattr(user, 'is_super_admin', False) or getattr(user, 'is_staff', False):
            return SupportTicket.objects.all().order_by('-created_at')
            
        # Hospital staff/patients see their own raised support tickets
        return SupportTicket.objects.filter(email=user.email).order_by('-created_at')

    def perform_create(self, serializer):
        user = self.request.user
        if user and not user.is_anonymous:
            hospital_node = getattr(user, 'hospital', None)
            user_name = getattr(user, 'name', 'Registered User')
            instance = serializer.save(
                hospital=hospital_node,
                email=user.email,
                name=user_name
            )
        else:
            instance = serializer.save()

        # Send confirmation email on registration
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            send_mail(
                subject=f"[eDoc HMS Support] Ticket Registered: {instance.subject}",
                message=f"Hi {instance.name},\n\nWe have received your support ticket request (Ref: #TKT-{instance.id}). Our technical command desk has been notified and is currently analyzing your request.\n\nTicket Summary:\nSubject: {instance.subject}\nMessage: {instance.message}\n\nWarm regards,\neDoc Technical Operations Support Team",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                fail_silently=True
            )
        except Exception:
            pass

    def perform_update(self, serializer):
        old_instance = self.get_object()
        instance = serializer.save()

        # Notify user when ticket status turns resolved
        if old_instance.status != 'resolved' and instance.status == 'resolved':
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                send_mail(
                    subject=f"[eDoc HMS Support] Ticket Resolved: {instance.subject}",
                    message=f"Hi {instance.name},\n\nGood news! Your support ticket (Ref: #TKT-{instance.id}) has been marked as RESOLVED by our platform administrators.\n\nTicket Summary:\nSubject: {instance.subject}\nStatus: RESOLVED\n\nIf you have any further questions, please raise a new support ticket.\n\nWarm regards,\neDoc Technical Operations Support Team",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.email],
                    fail_silently=True
                )
            except Exception:
                pass
