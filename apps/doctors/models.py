"""
Doctor Models
Maps the PHP 'doctor' and 'specialties' tables to Django ORM
"""
from django.db import models
from authentication.models import WebUser


class Specialty(models.Model):
    """Medical specialties (56 records from original SQL)."""
    name = models.CharField(max_length=100)

    objects = models.Manager()
    DoesNotExist: type[models.ObjectDoesNotExist]

    class Meta:
        db_table = 'specialties'
        verbose_name_plural = 'Specialties'
        ordering = ['name']

    def __str__(self) -> str:
        return str(self.name)


class Doctor(models.Model):
    """
    Doctor profile linked to WebUser.
    Corresponds to PHP 'doctor' table.
    """
    user = models.OneToOneField(
        WebUser,
        on_delete=models.CASCADE,
        related_name='doctor_profile',
        null=True, blank=True
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    nic = models.CharField(max_length=15, blank=True)
    telephone = models.CharField(max_length=15, blank=True)
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doctors'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    DoesNotExist: type[models.ObjectDoesNotExist]

    class Meta:
        db_table = 'doctor'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Dr. {self.name}"


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    ]
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='leave_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leave_request'
        ordering = ['-created_at']

    def __str__(self):
        return f"Leave Request: Dr. {self.doctor.name} ({self.start_date} to {self.end_date}) - {self.status}"

