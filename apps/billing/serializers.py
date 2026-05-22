from rest_framework import serializers
from .models import Invoice, InvoiceItem

class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['id', 'name', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['id', 'total_price']


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_email = serializers.CharField(source='patient.email', read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'hospital', 'patient', 'patient_name', 'patient_email',
            'billing_type', 'subtotal', 'discount', 'tax', 'total_amount',
            'status', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'hospital', 'total_amount', 'created_at', 'updated_at']
