"""
Appointment Service Layer
Handles booking logic with race-condition safe atomic transactions
"""
import logging
from django.db import transaction
from django.utils import timezone
from .models import Appointment
from schedules.models import Schedule
from patients.models import Patient

logger = logging.getLogger('edoc_hms')


class AppointmentService:

    @staticmethod
    @transaction.atomic
    def book_appointment(patient, schedule_id):
        """
        Book an appointment for a patient.
        Uses SELECT FOR UPDATE to prevent double-booking race conditions.
        Returns the created Appointment.
        """
        # Lock the schedule row to prevent concurrent booking
        schedule = Schedule.objects.select_for_update().get(pk=schedule_id)

        if schedule.is_full:
            raise ValueError('This session is fully booked.')

        # Check if patient already booked this session
        if Appointment.objects.filter(patient=patient, schedule=schedule).exists():
            raise ValueError('You have already booked this session.')

        # Determine next appointment number
        next_num = schedule.booked_count + 1

        appointment = Appointment.objects.create(
            patient=patient,
            schedule=schedule,
            appointment_number=next_num,
            appointment_date=timezone.now().date(),
        )

        # Automatically create paid OPD consultation invoice acting as a receipt
        hospital = None
        if schedule.doctor.user and schedule.doctor.user.hospital:
            hospital = schedule.doctor.user.hospital
        elif patient.user and patient.user.hospital:
            hospital = patient.user.hospital

        if hospital:
            try:
                from billing.models import Invoice, InvoiceItem
                fee = 500.00  # Rs 500 / $50 consultation fee
                invoice = Invoice.objects.create(
                    hospital=hospital,
                    patient=patient,
                    billing_type='opd',
                    subtotal=fee,
                    discount=0.00,
                    tax=0.00,
                    total_amount=fee,
                    status='paid'
                )
                InvoiceItem.objects.create(
                    invoice=invoice,
                    name=f"OPD Consultation - Dr. {schedule.doctor.name} ({schedule.title})",
                    quantity=1,
                    unit_price=fee
                )
                logger.info(f"Auto-generated Paid OPD Consultation Invoice #{invoice.id} for Appointment #{next_num}")
            except Exception as e:
                logger.error(f"Failed to generate auto OPD invoice: {str(e)}")

        logger.info(f"Appointment #{next_num} booked: {patient.name} for {schedule.title}")
        return appointment

    @staticmethod
    def cancel_appointment(appointment):
        """Cancel/delete an appointment."""
        appt_info = f"#{appointment.appointment_number} for {appointment.patient.name}"
        appointment.delete()
        logger.info(f"Appointment cancelled: {appt_info}")
