"""
Lab Models — Laboratory tests, sample logging, and result reporting
"""
from django.db import models
from django.utils import timezone


class LabTest(models.Model):
    from hospitals.models import Hospital
    hospital = models.ForeignKey(
        'hospitals.Hospital',
        on_delete=models.CASCADE,
        related_name='lab_tests',
        null=True, blank=True
    )
    name = models.CharField(max_length=255)
    test_code = models.CharField(max_length=50, help_text="e.g. CBC, LFT, TSH")
    description = models.TextField(blank=True)
    sample_type = models.CharField(max_length=100, help_text="e.g. Blood, Urine, Saliva", default="Blood")
    reference_range = models.TextField(help_text="Standard normal ranges for the report")
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lab_test_catalog'
        ordering = ['name']
        unique_together = ('hospital', 'test_code')

    def __str__(self):
        return f"{self.name} ({self.test_code})"


class LabRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Sample Collection'),
        ('collected', 'Sample Collected / Processing'),
        ('completed', 'Completed / Result Released'),
        ('cancelled', 'Cancelled'),
    ]

    hospital = models.ForeignKey(
        'hospitals.Hospital',
        on_delete=models.CASCADE,
        related_name='lab_requests',
        null=True, blank=True
    )
    test = models.ForeignKey(
        LabTest,
        on_delete=models.PROTECT,
        related_name='requests'
    )
    patient_name = models.CharField(max_length=255)
    prescribed_by = models.CharField(max_length=255, blank=True, help_text="Doctor who requested this test")
    sample_barcode = models.CharField(max_length=100, blank=True, help_text="Unique sample tracker ID")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Results & Reporting
    test_result = models.TextField(blank=True, help_text="Conducted test outcome findings / values")
    technician_notes = models.TextField(blank=True, help_text="Lab analyst observations")
    
    requested_at = models.DateTimeField(auto_now_add=True)
    sample_collected_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'lab_requests'
        ordering = ['-requested_at']

    def __str__(self):
        return f"LabReq #{self.id} — {self.test.test_code} for {self.patient_name}"
