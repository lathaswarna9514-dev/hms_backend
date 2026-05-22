"""
Pharmacy Serializers
"""
from rest_framework import serializers
from .models import MedicineCategory, Medicine, DispenseOrder


class MedicineCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineCategory
        fields = ['id', 'name', 'description']


class MedicineSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    is_low_stock = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Medicine
        fields = [
            'id', 'hospital', 'category', 'category_name',
            'name', 'generic_name', 'manufacturer',
            'unit', 'unit_price', 'stock_quantity', 'reorder_level',
            'expiry_date', 'is_active', 'is_low_stock', 'is_expired',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DispenseOrderSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    medicine_unit = serializers.CharField(source='medicine.unit', read_only=True)

    class Meta:
        model = DispenseOrder
        fields = [
            'id', 'medicine', 'medicine_name', 'medicine_unit',
            'patient_name', 'quantity', 'unit_price', 'total_price',
            'prescribed_by', 'notes', 'status', 'dispensed_at', 'created_at'
        ]
        read_only_fields = ['id', 'total_price', 'created_at']


class DispenseOrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispenseOrder
        fields = ['medicine', 'patient_name', 'quantity', 'prescribed_by', 'notes']

    def validate(self, data):
        medicine = data['medicine']
        qty = data['quantity']
        if medicine.stock_quantity < qty:
            raise serializers.ValidationError(
                f"Insufficient stock. Available: {medicine.stock_quantity} {medicine.unit}(s)."
            )
        return data

    def create(self, validated_data):
        medicine = validated_data['medicine']
        qty = validated_data['quantity']
        # Set pricing from current medicine price
        validated_data['unit_price'] = medicine.unit_price
        validated_data['total_price'] = medicine.unit_price * qty
        validated_data['status'] = 'dispensed'
        # Deduct stock
        medicine.stock_quantity -= qty
        medicine.save()
        return super().create(validated_data)
