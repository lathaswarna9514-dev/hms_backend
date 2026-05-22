from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SystemStatusView, 
    AttendanceViewSet,
    AuditLogView,
    BroadcastMessageView,
    ContentManagementView,
    QRCodeGeneratorView
)

app_name = 'common'

router = DefaultRouter()
router.register(r'attendance', AttendanceViewSet, basename='attendance')

urlpatterns = [
    path('status/', SystemStatusView.as_view(), name='status'),
    path('audit-logs/', AuditLogView.as_view(), name='audit_logs'),
    path('broadcast/', BroadcastMessageView.as_view(), name='broadcast'),
    path('cms/', ContentManagementView.as_view(), name='cms'),
    path('qr-generate/', QRCodeGeneratorView.as_view(), name='qr_generate'),
    path('', include(router.urls)),
]

