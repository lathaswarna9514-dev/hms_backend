"""
Schedule Serializers
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Schedule, Shift
from doctors.serializers import DoctorListSerializer


class ScheduleListSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    booked_count = serializers.IntegerField(read_only=True)
    available_slots = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)

    class Meta:
        model = Schedule
        fields = [
            'id', 'title', 'doctor', 'doctor_name',
            'schedule_date', 'schedule_time',
            'max_patients', 'booked_count', 'available_slots', 'is_full'
        ]


class ScheduleDetailSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    doctor_email = serializers.CharField(source='doctor.email', read_only=True)
    booked_count = serializers.IntegerField(read_only=True)
    available_slots = serializers.IntegerField(read_only=True)

    class Meta:
        model = Schedule
        fields = [
            'id', 'title', 'doctor', 'doctor_name', 'doctor_email',
            'schedule_date', 'schedule_time',
            'max_patients', 'booked_count', 'available_slots', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ScheduleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ['title', 'doctor', 'schedule_date', 'schedule_time', 'max_patients']

    def validate_schedule_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError('Schedule date cannot be in the past.')
        return value


class ScheduleBookingInfoSerializer(serializers.ModelSerializer):
    """Minimal data for patient booking confirmation page."""
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    doctor_email = serializers.CharField(source='doctor.email', read_only=True)
    next_appointment_number = serializers.SerializerMethodField()

    class Meta:
        model = Schedule
        fields = [
            'id', 'title', 'doctor_name', 'doctor_email',
            'schedule_date', 'schedule_time',
            'next_appointment_number', 'available_slots'
        ]

    def get_next_appointment_number(self, obj):
        return obj.booked_count + 1


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ['id', 'hospital', 'name', 'start_time', 'end_time', 'created_at', 'updated_at']
        read_only_fields = ['id', 'hospital', 'created_at', 'updated_at']

