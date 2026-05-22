"""
Doctor Serializers
"""
from rest_framework import serializers
from .models import Doctor, Specialty
from authentication.models import WebUser

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ['id', 'name']


class DoctorListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    specialty_name = serializers.CharField(source='specialty.name', read_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'name', 'email', 'specialty', 'specialty_name', 'telephone']


class DoctorDetailSerializer(serializers.ModelSerializer):
    """Full doctor details."""
    specialty_name = serializers.CharField(source='specialty.name', read_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'name', 'email', 'nic', 'telephone', 'specialty', 'specialty_name', 'created_at']
        read_only_fields = ['id', 'created_at']


class DoctorCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new doctor (admin only)."""
    password = serializers.CharField(write_only=True, min_length=3)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = Doctor
        fields = ['name', 'email', 'nic', 'telephone', 'specialty', 'password', 'confirm_password']

    def validate_email(self, value):
        if WebUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs


class DoctorUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating doctor details."""
    password = serializers.CharField(write_only=True, required=False, min_length=3)
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Doctor
        fields = ['name', 'email', 'nic', 'telephone', 'specialty', 'password', 'confirm_password']

    def validate(self, attrs):
        if attrs.get('password') and attrs['password'] != attrs.get('confirm_password', ''):
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs


from .models import LeaveRequest

class LeaveRequestSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)

    class Meta:
        model = LeaveRequest
        fields = ['id', 'doctor', 'doctor_name', 'start_date', 'end_date', 'reason', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'doctor', 'created_at', 'updated_at']

