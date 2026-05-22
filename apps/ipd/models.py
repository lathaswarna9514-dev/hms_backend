"""
IPD Models — Inpatient Department
Handles patient admissions, ward assignment, and discharge records.
"""
from django.db import models
from django.utils import timezone
from patients.models import Patient
from rooms_beds.models import Bed
from doctors.models import Doctor


class IPDAdmission(models.Model):
    """
    Tracks a patient's entire inpatient stay from admission to discharge.
    """
    STATUS_CHOICES = [
        ('admitted', 'Admitted'),
        ('discharged', 'Discharged'),
        ('transferred', 'Transferred'),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='ipd_admissions'
    )
    attending_doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ipd_admissions'
    )
    bed = models.ForeignKey(
        Bed,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ipd_admissions'
    )
    admission_date = models.DateTimeField(default=timezone.now)
    discharge_date = models.DateTimeField(null=True, blank=True)
    diagnosis = models.TextField(blank=True)
    admission_notes = models.TextField(blank=True)
    discharge_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='admitted')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ipd_admissions'
        ordering = ['-admission_date']

    def __str__(self):
        return f"IPD#{self.id} — {self.patient.name} [{self.status}]"


class VitalRecord(models.Model):
    """
    Nurse-recorded patient vitals (BP, pulse, temperature, SpO2, etc.)
    Recorded at each nursing round.
    """
    admission = models.ForeignKey(
        IPDAdmission,
        on_delete=models.CASCADE,
        related_name='vitals'
    )
    recorded_at = models.DateTimeField(default=timezone.now)
    blood_pressure_systolic = models.PositiveIntegerField(null=True, blank=True, help_text='mmHg')
    blood_pressure_diastolic = models.PositiveIntegerField(null=True, blank=True, help_text='mmHg')
    pulse_rate = models.PositiveIntegerField(null=True, blank=True, help_text='bpm')
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='°F')
    spo2 = models.PositiveIntegerField(null=True, blank=True, help_text='SpO2 %')
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True, help_text='breaths/min')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ipd_vitals'
        ordering = ['-recorded_at']

    def __str__(self):
        return f"Vitals for {self.admission.patient.name} @ {self.recorded_at}"
