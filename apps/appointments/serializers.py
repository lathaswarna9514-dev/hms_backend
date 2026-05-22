"""
Appointment Serializers
"""
from rest_framework import serializers
from .models import Appointment


class AppointmentListSerializer(serializers.ModelSerializer):
    """For admin: shows patient + schedule details."""
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_telephone = serializers.CharField(source='patient.telephone', read_only=True)
    doctor_name = serializers.CharField(source='schedule.doctor.name', read_only=True)
    session_title = serializers.CharField(source='schedule.title', read_only=True)
    schedule_date = serializers.DateField(source='schedule.schedule_date', read_only=True)
    schedule_time = serializers.TimeField(source='schedule.schedule_time', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'appointment_number',
            'patient', 'patient_name', 'patient_telephone',
            'schedule', 'doctor_name', 'session_title',
            'schedule_date', 'schedule_time',
            'appointment_date', 'booked_at'
        ]


class AppointmentInScheduleSerializer(serializers.ModelSerializer):
    """Used in schedule detail view to show patients booked in a session."""
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_id = serializers.IntegerField(source='patient.id', read_only=True)
    patient_telephone = serializers.CharField(source='patient.telephone', read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'patient_id', 'patient_name', 'patient_telephone', 'appointment_number']


class AppointmentCreateSerializer(serializers.Serializer):
    """Patient booking a session."""
    schedule_id = serializers.IntegerField()

    def validate_schedule_id(self, value):
        from schedules.models import Schedule
        try:
            schedule = Schedule.objects.get(pk=value)
        except Schedule.DoesNotExist:
            raise serializers.ValidationError('Session not found.')

        if schedule.is_full:
            raise serializers.ValidationError('This session is fully booked.')

        return value


class AppointmentPatientSerializer(serializers.ModelSerializer):
    """Patient's own booking view."""
    doctor_name = serializers.CharField(source='schedule.doctor.name', read_only=True)
    doctor_email = serializers.CharField(source='schedule.doctor.email', read_only=True)
    session_title = serializers.CharField(source='schedule.title', read_only=True)
    schedule_date = serializers.DateField(source='schedule.schedule_date', read_only=True)
    schedule_time = serializers.TimeField(source='schedule.schedule_time', read_only=True)
    specialty = serializers.CharField(source='schedule.doctor.specialty.name', read_only=True)
    hospital_name = serializers.SerializerMethodField()
    hospital_phone = serializers.SerializerMethodField()
    hospital_address = serializers.SerializerMethodField()
    hospital_email = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id', 'appointment_number',
            'session_title', 'doctor_name', 'doctor_email', 'specialty',
            'schedule_date', 'schedule_time',
            'appointment_date', 'booked_at',
            'hospital_name', 'hospital_phone', 'hospital_address', 'hospital_email'
        ]

    def get_hospital_name(self, obj):
        h = getattr(obj.schedule.doctor.user, 'hospital', None)
        return h.name if h else "General Hospital"

    def get_hospital_phone(self, obj):
        h = getattr(obj.schedule.doctor.user, 'hospital', None)
        return h.phone if h else ""

    def get_hospital_address(self, obj):
        h = getattr(obj.schedule.doctor.user, 'hospital', None)
        return h.address if h else ""

    def get_hospital_email(self, obj):
        h = getattr(obj.schedule.doctor.user, 'hospital', None)
        return h.email if h else ""
