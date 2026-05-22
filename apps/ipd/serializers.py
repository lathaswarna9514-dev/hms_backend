"""
IPD Serializers
"""
from rest_framework import serializers
from .models import IPDAdmission, VitalRecord


class VitalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = VitalRecord
        fields = [
            'id', 'admission', 'recorded_at',
            'blood_pressure_systolic', 'blood_pressure_diastolic',
            'pulse_rate', 'temperature', 'spo2', 'respiratory_rate',
            'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class IPDAdmissionListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    doctor_name = serializers.CharField(source='attending_doctor.name', read_only=True, default='')
    bed_label = serializers.CharField(source='bed.bed_number', read_only=True, default='')
    room_label = serializers.CharField(source='bed.room.room_number', read_only=True, default='')

    class Meta:
        model = IPDAdmission
        fields = [
            'id', 'patient_name', 'doctor_name',
            'bed_label', 'room_label',
            'admission_date', 'status', 'diagnosis'
        ]


class IPDAdmissionDetailSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    doctor_name = serializers.CharField(source='attending_doctor.name', read_only=True, default='')
    bed_label = serializers.CharField(source='bed.bed_number', read_only=True, default='')
    room_label = serializers.CharField(source='bed.room.room_number', read_only=True, default='')
    vitals = VitalRecordSerializer(many=True, read_only=True)

    class Meta:
        model = IPDAdmission
        fields = [
            'id', 'patient', 'patient_name',
            'attending_doctor', 'doctor_name',
            'bed', 'bed_label', 'room_label',
            'admission_date', 'discharge_date',
            'diagnosis', 'admission_notes', 'discharge_notes',
            'status', 'vitals', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class IPDAdmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPDAdmission
        fields = [
            'patient', 'attending_doctor', 'bed',
            'admission_date', 'diagnosis', 'admission_notes'
        ]
