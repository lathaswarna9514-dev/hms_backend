"""
Patient Models
Maps the PHP 'patient' table to Django ORM
"""
from django.db import models
from authentication.models import WebUser


class Patient(models.Model):
    """
    Patient profile linked to WebUser.
    Corresponds to PHP 'patient' table.
    """
    user = models.OneToOneField(
        WebUser,
        on_delete=models.CASCADE,
        related_name='patient_profile',
        null=True, blank=True
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    address = models.CharField(max_length=255, blank=True)
    nic = models.CharField(max_length=15, blank=True)
    dob = models.DateField(null=True, blank=True)
    telephone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    DoesNotExist: type[models.ObjectDoesNotExist]

    class Meta:
        db_table = 'patient'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return str(self.name)


