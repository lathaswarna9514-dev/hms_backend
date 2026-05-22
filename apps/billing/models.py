from django.db import models
from hospitals.models import Hospital
from patients.models import Patient

class Invoice(models.Model):
    BILLING_TYPES = [
        ('opd', 'Outpatient Department (OPD)'),
        ('ipd', 'Inpatient Department (IPD)'),
        ('general', 'General / Pharmacy / Lab'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='invoices')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='invoices')
    billing_type = models.CharField(max_length=20, choices=BILLING_TYPES, default='general')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_invoices'
        ordering = ['-created_at']

    def __str__(self):
        return f"Inv #{self.id} — {self.patient.name} (${self.total_amount})"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'billing_invoice_items'

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} × {self.quantity}"
