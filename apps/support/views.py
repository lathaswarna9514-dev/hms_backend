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
            qs = SupportTicket.objects.all().order_by('-created_at')
        else:
            # Hospital staff/patients see their own raised support tickets
            qs = SupportTicket.objects.filter(email=user.email).order_by('-created_at')

        # Add filtering & search
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)

        search_param = self.request.query_params.get('search')
        if search_param:
            from django.db.models import Q
            qs = qs.filter(
                Q(subject__icontains=search_param) |
                Q(email__icontains=search_param) |
                Q(name__icontains=search_param)
            )
        return qs

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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # Calculate global counts for the filtered base queryset (before pagination)
        pending_count = queryset.exclude(status='resolved').count()
        resolved_count = queryset.filter(status='resolved').count()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['pending_count'] = pending_count
            response.data['resolved_count'] = resolved_count
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'count': queryset.count(),
            'pending_count': pending_count,
            'resolved_count': resolved_count,
            'results': serializer.data
        })
