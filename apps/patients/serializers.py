"""
Patient Serializers
"""
from rest_framework import serializers
from .models import Patient


class PatientListSerializer(serializers.ModelSerializer):
    """Lightweight list serializer."""
    class Meta:
        model = Patient
        fields = ['id', 'name', 'email', 'telephone', 'dob']


class PatientDetailSerializer(serializers.ModelSerializer):
    """Full patient profile."""
    class Meta:
        model = Patient
        fields = ['id', 'name', 'email', 'address', 'nic', 'dob', 'telephone', 'created_at']
        read_only_fields = ['id', 'created_at']


class PatientUpdateSerializer(serializers.ModelSerializer):
    """For patients updating their own settings."""
    password = serializers.CharField(write_only=True, required=False, min_length=3)
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Patient
        fields = ['name', 'address', 'nic', 'dob', 'telephone', 'password', 'confirm_password']

    def validate(self, attrs):
        if attrs.get('password') and attrs['password'] != attrs.get('confirm_password', ''):
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs
