import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    CustomTokenObtainPairSerializer,
    PatientRegisterSerializer,
    SuperAdminVerifyOTPSerializer,
    StaffSerializer,
    SuperAdminStaffSerializer
)
from .services import AuthService
from .models import WebUser

logger = logging.getLogger('edoc_hms')

class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Overrides simplejwt TokenObtainPairView.
    If credentials match and role is 'super-admin', sends OTP and signals 2FA required.
    Otherwise returns access and refresh JWT tokens.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response(
                {'success': False, 'message': 'Invalid email or password.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.user
        validated_data = serializer.validated_data

        if validated_data.get('require_2fa'):
            # Trigger Super Admin 2FA flow
            otp = AuthService.generate_otp(user)
            email_sent = AuthService.send_otp_email(otp)
            
            if email_sent:
                return Response({
                    'success': True,
                    'require_2fa': True,
                    'message': 'Verification code sent to your email.'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Failed to send verification code. Please contact system support.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'success': True,
            'require_2fa': False,
            'data': validated_data
        }, status=status.HTTP_200_OK)


class SuperAdminVerifyOTPView(APIView):
    """
    POST /api/auth/verify-otp/
    Validates Super Admin 2FA OTP code. Returns JWT tokens on success.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SuperAdminVerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        otp_code = serializer.validated_data['otp_code']

        success, message = AuthService.verify_otp(user, otp_code)
        if not success:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        refresh['role'] = user.usertype
        refresh['usertype'] = 'sa'
        refresh['email'] = user.email
        refresh['name'] = user.name
        refresh['hospital_id'] = None

        return Response({
            'success': True,
            'data': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'role': user.usertype,
                    'usertype': 'sa',
                    'name': user.name,
                    'hospital_id': None
                }
            }
        }, status=status.HTTP_200_OK)


class SuperAdminResendOTPView(APIView):
    """
    POST /api/auth/resend-otp/
    Resends OTP verification email to Super Admin.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                'success': False,
                'message': 'Email address is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = WebUser.objects.get(email=email, usertype='super-admin')
        except WebUser.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Super Admin user not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        otp = AuthService.generate_otp(user)
        email_sent = AuthService.send_otp_email(otp)
        
        if email_sent:
            return Response({
                'success': True,
                'message': 'Verification code resent successfully.'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Failed to send verification code.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PatientRegisterView(APIView):
    """
    POST /api/auth/register/
    Self sign-up endpoint for patients.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PatientRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        
        # Auto-login after registration
        refresh = RefreshToken.for_user(user)
        refresh['role'] = user.usertype
        refresh['usertype'] = 'p'
        refresh['email'] = user.email
        refresh['name'] = user.name
        refresh['hospital_id'] = None

        return Response({
            'success': True,
            'message': 'Patient registration successful.',
            'data': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'role': user.usertype,
                    'usertype': 'p',
                    'name': user.name,
                    'hospital_id': None
                }
            }
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklists SimpleJWT refresh tokens.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({
                'success': False,
                'message': 'Refresh token is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                'success': True,
                'message': 'Logged out successfully.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to blacklist token.'
            }, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """
    GET /api/auth/profile/
    Returns currently logged in user info.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        role_map = {
            'super-admin': 'sa',
            'hospital-admin': 'a',
            'doctor': 'd',
            'patient': 'p',
            'nurse': 'n',
            'frontdesk': 'r',
            'lab': 'l',
            'pharmacy': 'ph'
        }
        legacy_usertype = role_map.get(user.usertype, user.usertype)
        return Response({
            'success': True,
            'data': {
                'id': user.id,
                'email': user.email,
                'role': user.usertype,
                'usertype': legacy_usertype,
                'name': user.name,
                'hospital_name': user.hospital.name if user.hospital else None,
                'hospital_id': user.hospital.id if user.hospital else None
            }
        })


from rest_framework import viewsets
from utils.permissions import IsAdminUser

class StaffViewSet(viewsets.ModelViewSet):
    """
    CRUD Endpoint for Hospital Admin to manage their hospital staff members.
    """
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        hospital = self.request.hospital
        if not hospital:
            return WebUser.objects.none()
        qs = WebUser.objects.filter(hospital=hospital).exclude(
            usertype__in=['super-admin', 'patient']
        ).order_by('usertype', 'name')
        
        usertype_param = self.request.query_params.get('usertype')
        if usertype_param:
            legacy_map = {
                'sa': 'super-admin',
                'a': 'hospital-admin',
                'd': 'doctor',
                'p': 'patient',
                'n': 'nurse',
                'r': 'frontdesk',
                'l': 'lab',
                'ph': 'pharmacy'
            }
            mapped_type = legacy_map.get(usertype_param, usertype_param)
            qs = qs.filter(usertype=mapped_type)
        return qs

    def perform_create(self, serializer):
        # Automatically tie the staff member to the admin's hospital
        serializer.save(hospital=self.request.hospital)


from utils.permissions import IsSuperAdmin

class SuperAdminStaffViewSet(viewsets.ModelViewSet):
    """
    CRUD Endpoint for Super Admin to manage staff credentials for any hospital.
    """
    serializer_class = SuperAdminStaffSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def get_queryset(self):
        qs = WebUser.objects.exclude(usertype__in=['super-admin', 'patient']).order_by('-date_joined')
        usertype_param = self.request.query_params.get('usertype')
        if usertype_param:
            legacy_map = {
                'sa': 'super-admin',
                'a': 'hospital-admin',
                'd': 'doctor',
                'p': 'patient',
                'n': 'nurse',
                'r': 'frontdesk',
                'l': 'lab',
                'ph': 'pharmacy'
            }
            mapped_type = legacy_map.get(usertype_param, usertype_param)
            qs = qs.filter(usertype=mapped_type)
        return qs


class SuperAdminEmailView(APIView):
    """
    GET /api/auth/super-admin-email/
    Returns the configured super admin email from settings (EMAIL_HOST_USER).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from django.conf import settings
        email = getattr(settings, 'EMAIL_HOST_USER', None)
        return Response({
            'success': True,
            'email': email
        }, status=status.HTTP_200_OK)
class PlatformAdminsViewSet(viewsets.ModelViewSet):
    """
    CRUD Endpoint for Super Admin to manage other Platform Admins (super-admins).
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def get_queryset(self):
        from authentication.models import WebUser
        return WebUser.objects.filter(usertype='super-admin').order_by('-date_joined')

    # We can reuse SuperAdminStaffSerializer or create a new one, but for now we return a simple response
    def get_serializer_class(self):
        from .serializers import SuperAdminStaffSerializer
        return SuperAdminStaffSerializer
