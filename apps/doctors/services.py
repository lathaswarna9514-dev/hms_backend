"""
Doctor Service Layer
Business logic for doctor management
"""
import logging
from django.db import transaction
from .models import Doctor, Specialty
from authentication.models import WebUser

logger = logging.getLogger('edoc_hms')


class DoctorService:
    """Handles doctor CRUD business logic."""

    @staticmethod
    def get_all_doctors(search=None):
        """Return all doctors, optionally filtered by name/email."""
        qs = Doctor.objects.select_related('specialty').all()
        if search:
            qs = qs.filter(
                models.Q(name__icontains=search) |
                models.Q(email__icontains=search)
            )
        return qs

    @staticmethod
    @transaction.atomic
    def create_doctor(validated_data, hospital=None):
        """
        Create a new doctor:
        1. Create WebUser account
        2. Create Doctor profile
        """
        email = validated_data['email']
        password = validated_data.pop('password')
        validated_data.pop('confirm_password', None)

        user = WebUser.objects.create_user(
            email=email,
            password=password,
            usertype='doctor',
            hospital=hospital
        )

        doctor = Doctor.objects.create(
            user=user,
            email=email,
            **validated_data
        )
        logger.info(f"Doctor created: {email}")
        return doctor

    @staticmethod
    @transaction.atomic
    def update_doctor(doctor, validated_data):
        """Update doctor and optionally change password."""
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)

        new_email = validated_data.get('email', doctor.email)

        # Update doctor profile
        for field, value in validated_data.items():
            setattr(doctor, field, value)
        doctor.save()

        # Update linked user
        if doctor.user:
            if new_email != doctor.user.email:
                doctor.user.email = new_email
            if password:
                doctor.user.set_password(password)
            doctor.user.save()

        logger.info(f"Doctor updated: {doctor.email}")
        return doctor

    @staticmethod
    @transaction.atomic
    def delete_doctor(doctor):
        """Delete doctor and their WebUser account."""
        email = doctor.email
        if doctor.user:
            doctor.user.delete()  # Cascades to delete doctor profile
        else:
            doctor.delete()
        logger.info(f"Doctor deleted: {email}")


from django.db import models  # noqa - needed for Q above
