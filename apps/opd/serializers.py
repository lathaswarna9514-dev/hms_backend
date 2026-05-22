from rest_framework import serializers
from .models import Prescription

class PrescriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'appointment', 'diagnosis', 'symptoms', 'medicines',
            'suggested_tests', 'advice', 'diet_advice', 'follow_up_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class PrescriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = [
            'id', 'patient', 'doctor', 'appointment', 'diagnosis',
            'symptoms', 'medicines', 'suggested_tests', 'advice',
            'diet_advice', 'follow_up_date'
        ]
