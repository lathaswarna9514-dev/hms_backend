from django.urls import path
from .views import (
    AdminDashboardView,
    PatientDashboardView,
    DoctorDashboardView,
    SuperAdminDashboardView,
    HospitalAdminAnalyticsView,
    SuperAdminAnalyticsView
)

urlpatterns = [
    path('admin/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/analytics/', HospitalAdminAnalyticsView.as_view(), name='admin_analytics'),
    path('patient/', PatientDashboardView.as_view(), name='patient_dashboard'),
    path('doctor/', DoctorDashboardView.as_view(), name='doctor_dashboard'),
    path('super-admin/', SuperAdminDashboardView.as_view(), name='super_admin_dashboard'),
    path('super-admin/analytics/', SuperAdminAnalyticsView.as_view(), name='super_admin_analytics'),
]
