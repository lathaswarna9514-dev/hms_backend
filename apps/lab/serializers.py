"""
Lab Serializers
"""
from rest_framework import serializers
from .models import LabTest, LabRequest


class LabTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTest
        fields = [
            'id', 'hospital', 'name', 'test_code',
            'description', 'sample_type', 'reference_range',
            'cost', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class LabRequestSerializer(serializers.ModelSerializer):
    test_name = serializers.CharField(source='test.name', read_only=True)
    test_code = serializers.CharField(source='test.test_code', read_only=True)
    sample_type = serializers.CharField(source='test.sample_type', read_only=True)
    cost = serializers.DecimalField(source='test.cost', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = LabRequest
        fields = [
            'id', 'hospital', 'test', 'test_name', 'test_code', 'sample_type', 'cost',
            'patient_name', 'prescribed_by', 'sample_barcode',
            'status', 'requested_at', 'sample_collected_at', 'completed_at'
        ]
        read_only_fields = ['id', 'requested_at']


class LabRequestDetailSerializer(serializers.ModelSerializer):
    test_name = serializers.CharField(source='test.name', read_only=True)
    test_code = serializers.CharField(source='test.test_code', read_only=True)
    sample_type = serializers.CharField(source='test.sample_type', read_only=True)
    reference_range = serializers.CharField(source='test.reference_range', read_only=True)
    cost = serializers.DecimalField(source='test.cost', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = LabRequest
        fields = [
            'id', 'hospital', 'test', 'test_name', 'test_code', 'sample_type', 'reference_range', 'cost',
            'patient_name', 'prescribed_by', 'sample_barcode', 'status',
            'test_result', 'technician_notes',
            'requested_at', 'sample_collected_at', 'completed_at'
        ]
        read_only_fields = ['id', 'requested_at']


class LabRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabRequest
        fields = ['test', 'patient_name', 'prescribed_by']
