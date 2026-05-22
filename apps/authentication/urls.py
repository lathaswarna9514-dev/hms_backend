from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView,
    SuperAdminVerifyOTPView,
    SuperAdminResendOTPView,
    PatientRegisterView,
    LogoutView,
    ProfileView,
    StaffViewSet,
    SuperAdminStaffViewSet,
    SuperAdminEmailView,
    PlatformAdminsViewSet
)

router = DefaultRouter()
router.register(r'staff', StaffViewSet, basename='staff')
router.register(r'super-admin/staff', SuperAdminStaffViewSet, basename='super-admin-staff')
router.register(r'super-admin/admins', PlatformAdminsViewSet, basename='super-admin-admins')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('verify-otp/', SuperAdminVerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', SuperAdminResendOTPView.as_view(), name='resend-otp'),
    path('register/', PatientRegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('super-admin-email/', SuperAdminEmailView.as_view(), name='super-admin-email'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('', include(router.urls)),
]

