"""
Appointment Models
Maps the PHP 'appointment' table to Django ORM
"""
from django.db import models
from django.utils import timezone
from patients.models import Patient
from schedules.models import Schedule


class Appointment(models.Model):
    APPOINTMENT_TYPE_CHOICES = [
        ('ONLINE', 'Online Consultation'),
        ('OFFLINE', 'In-Person / Walk-in')
    ]
    DEPARTMENT_TYPE_CHOICES = [
        ('OPD', 'Outpatient Department'),
        ('IPD', 'Inpatient Department')
    ]
    """
    Appointment/booking record.
    Corresponds to PHP 'appointment' table.
    """
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    appointment_number = models.PositiveIntegerField(
        help_text='Auto-assigned sequential booking number for this session'
    )
    appointment_date = models.DateField(default=timezone.now)
    appointment_type = models.CharField(max_length=10, choices=APPOINTMENT_TYPE_CHOICES, default='OFFLINE')
    department_type = models.CharField(max_length=10, choices=DEPARTMENT_TYPE_CHOICES, default='OPD')
    booked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'appointment'
        unique_together = [['schedule', 'appointment_number']]
        ordering = ['schedule__schedule_date', 'appointment_number']

    def __str__(self):
        return f"Appt #{self.appointment_number} - {self.patient.name} - {self.schedule.title}"
