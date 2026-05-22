from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import WebUser
from hospitals.models import Hospital

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom SimpleJWT TokenObtainPairSerializer to inject role, email, name, and hospital scoping claims.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

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

        # Inject custom claims
        token['role'] = user.usertype
        token['usertype'] = legacy_usertype
        token['email'] = user.email
        token['name'] = user.name
        token['hospital_id'] = user.hospital.id if user.hospital else None
        
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
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
        legacy_usertype = role_map.get(self.user.usertype, self.user.usertype)

        # Super-admin requires 2FA authentication, so we don't return tokens directly on login
        if self.user.usertype == 'super-admin':
            data['require_2fa'] = True
            # Strip tokens from response to prevent unauthorized session creation prior to 2FA verification
            data.pop('access', None)
            data.pop('refresh', None)
        else:
            data['require_2fa'] = False
            data['user'] = {
                'id': self.user.id,
                'email': self.user.email,
                'role': self.user.usertype,
                'usertype': legacy_usertype,
                'name': self.user.name,
                'hospital_id': self.user.hospital.id if self.user.hospital else None
            }
        return data


class PatientRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for Patient Registration (Self Sign-Up)
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = WebUser
        fields = ['email', 'name', 'password', 'confirm_password']

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = WebUser.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=password,
            usertype='patient'
        )
        return user


class SuperAdminVerifyOTPSerializer(serializers.Serializer):
    """
    Serializer to validate the OTP token sent to Super Admin
    """
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        email = attrs.get('email')
        otp_code = attrs.get('otp_code')

        try:
            user = WebUser.objects.get(email=email, usertype='super-admin')
        except WebUser.DoesNotExist:
            raise serializers.ValidationError('User not found.')

        attrs['user'] = user
        return attrs


class StaffSerializer(serializers.ModelSerializer):
    """
    Serializer for Hospital Admins to manage staff credentials.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = WebUser
        fields = ['id', 'email', 'name', 'usertype', 'password', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_usertype(self, value):
        allowed_roles = ['hospital-admin', 'frontdesk', 'doctor', 'nurse', 'pharmacy', 'lab']
        if value not in allowed_roles:
            raise serializers.ValidationError("Invalid staff role provided.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = WebUser.objects.create(
            email=validated_data['email'],
            name=validated_data['name'],
            usertype=validated_data['usertype'],
            is_active=validated_data.get('is_active', True)
        )
        user.set_password(password)
        user.save()
        return user


class SuperAdminStaffSerializer(serializers.ModelSerializer):
    """
    Serializer for Super Admins to manage staff credentials for any hospital.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    hospital = serializers.PrimaryKeyRelatedField(queryset=Hospital.objects.all(), required=True)
    hospital_name = serializers.SerializerMethodField()
    nic = serializers.SerializerMethodField()

    class Meta:
        model = WebUser
        fields = ['id', 'email', 'name', 'usertype', 'password', 'hospital', 'hospital_name', 'nic', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined', 'hospital_name', 'nic']

    def get_hospital_name(self, obj):
        return obj.hospital.name if obj.hospital else None

    def get_nic(self, obj):
        # WebUser doesn't have NIC; return None gracefully
        return getattr(obj, 'nic', None)

    def validate_usertype(self, value):
        allowed_roles = ['hospital-admin', 'frontdesk', 'doctor', 'nurse', 'pharmacy', 'lab']
        if value not in allowed_roles:
            raise serializers.ValidationError("Invalid staff role provided.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = WebUser.objects.create(
            email=validated_data['email'],
            name=validated_data['name'],
            usertype=validated_data['usertype'],
            hospital=validated_data['hospital'],
            is_active=validated_data.get('is_active', True)
        )
        user.set_password(password)
        user.save()
        return user

