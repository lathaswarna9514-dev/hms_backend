"""
Pharmacy Models — Medicine inventory and dispensing management
"""
from django.db import models
from django.utils import timezone


class MedicineCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'pharmacy_categories'
        verbose_name_plural = 'Medicine Categories'

    def __str__(self):
        return self.name


class Medicine(models.Model):
    UNIT_CHOICES = [
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('syrup', 'Syrup (ml)'),
        ('injection', 'Injection (ml)'),
        ('cream', 'Cream (g)'),
        ('drops', 'Drops'),
        ('sachet', 'Sachet'),
        ('inhaler', 'Inhaler'),
        ('other', 'Other'),
    ]

    from hospitals.models import Hospital
    hospital = models.ForeignKey(
        'hospitals.Hospital',
        on_delete=models.CASCADE,
        related_name='medicines',
        null=True, blank=True
    )
    category = models.ForeignKey(
        MedicineCategory,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='medicines'
    )
    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='tablet')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(
        default=20,
        help_text='Alert when stock falls below this quantity'
    )
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pharmacy_medicines'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.unit})"

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.reorder_level

    @property
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False


class DispenseOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('dispensed', 'Dispensed'),
        ('cancelled', 'Cancelled'),
    ]

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT,
        related_name='dispense_orders'
    )
    patient_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    prescribed_by = models.CharField(max_length=255, blank=True, help_text='Doctor name')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    dispensed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pharmacy_dispense_orders'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Dispense #{self.id} — {self.medicine.name} × {self.quantity}"
