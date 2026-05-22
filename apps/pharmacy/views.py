"""
Pharmacy Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import MedicineCategory, Medicine, DispenseOrder
from .serializers import (
    MedicineCategorySerializer, MedicineSerializer,
    DispenseOrderSerializer, DispenseOrderCreateSerializer
)

class MedicineCategoryViewSet(viewsets.ModelViewSet):
    """CRUD for medicine categories."""
    serializer_class = MedicineCategorySerializer
    permission_classes = [IsAuthenticated]
    queryset = MedicineCategory.objects.all().order_by('name')

    def get_permissions(self):
        # Only pharmacy staff and admins can manage categories
        return [IsAuthenticated()]

    def check_permission(self, request):
        user = request.user
        return user.is_admin or user.is_pharmacy

    def list(self, request, *args, **kwargs):
        if not self.check_permission(request):
            return Response({'success': False, 'message': 'Permission denied.'}, status=403)
        return super().list(request, *args, **kwargs)


class MedicineViewSet(viewsets.ModelViewSet):
    """
    CRUD for medicines — scoped to request.hospital.
    Pharmacy staff can manage stock; admins have full access.
    """
    serializer_class = MedicineSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not (user.is_admin or user.is_pharmacy or user.is_doctor):
            return Medicine.objects.none()

        hospital = self.request.hospital
        qs = Medicine.objects.select_related('category').all()
        if hospital:
            qs = qs.filter(hospital=hospital)

        # Filters
        search = self.request.query_params.get('search')
        low_stock = self.request.query_params.get('low_stock')
        category = self.request.query_params.get('category')

        if search:
            qs = qs.filter(name__icontains=search)
        if low_stock:
            from django.db.models import F
            qs = qs.filter(stock_quantity__lte=F('reorder_level'))
        if category:
            qs = qs.filter(category_id=category)

        return qs

    def perform_create(self, serializer):
        hospital = self.request.hospital
        serializer.save(hospital=hospital)

    @action(detail=True, methods=['post'], url_path='restock')
    def restock(self, request, pk=None):
        """POST /api/pharmacy/medicines/<id>/restock/ — Add stock quantity."""
        medicine = self.get_object()
        qty = request.data.get('quantity', 0)
        try:
            qty = int(qty)
            if qty <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({'success': False, 'message': 'Invalid quantity.'}, status=400)

        medicine.stock_quantity += qty
        medicine.save()
        return Response({
            'success': True,
            'message': f'Added {qty} units. New stock: {medicine.stock_quantity}.',
            'stock_quantity': medicine.stock_quantity
        })


class DispenseOrderViewSet(viewsets.ModelViewSet):
    """
    Dispensing orders — pharmacy staff create, admin can list all.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return DispenseOrderCreateSerializer
        return DispenseOrderSerializer

    def get_queryset(self):
        user = self.request.user
        if not (user.is_admin or user.is_pharmacy):
            return DispenseOrder.objects.none()

        hospital = self.request.hospital
        qs = DispenseOrder.objects.select_related('medicine').all()
        if hospital:
            qs = qs.filter(medicine__hospital=hospital)

        status_filter = self.request.query_params.get('status')
        search = self.request.query_params.get('search')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(patient_name__icontains=search)

        return qs

    @action(detail=True, methods=['post'], url_path='dispense')
    def dispense(self, request, pk=None):
        """POST /api/pharmacy/orders/<id>/dispense/ — Dispense the medicine and deduct stock."""
        from django.utils import timezone
        order = self.get_object()
        if order.status != 'pending':
            return Response({
                'success': False,
                'message': f'Order is already {order.status} and cannot be dispensed.'
            }, status=status.HTTP_400_BAD_REQUEST)

        medicine = order.medicine
        if medicine.stock_quantity < order.quantity:
            return Response({
                'success': False,
                'message': f'Insufficient stock. Available: {medicine.stock_quantity}, Required: {order.quantity}.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Deduct stock and save
        medicine.stock_quantity -= order.quantity
        medicine.save()

        # Update order status and timestamp
        order.status = 'dispensed'
        order.dispensed_at = timezone.now()
        order.save()

        return Response({
            'success': True,
            'message': 'Medicine dispensed successfully.',
            'data': DispenseOrderSerializer(order).data
        })
