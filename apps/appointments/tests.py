from django.test import TestCase
from django.utils import timezone
from datetime import date
from authentication.models import WebUser
from hospitals.models import Hospital
from patients.models import Patient
from doctors.models import Doctor
from schedules.models import Schedule
from appointments.services import AppointmentService
from billing.models import Invoice, InvoiceItem

class AppointmentServiceTestCase(TestCase):
    def setUp(self):
        # Create a mock hospital
        self.hospital = Hospital.objects.create(
            name="Test General Hospital",
            address="123 Health Ave"
        )
        
        # Create user accounts for doctor and patient
        self.doc_user = WebUser.objects.create_user(
            email="doc@test.com",
            password="testpassword123",
            usertype="doctor",
            name="Gregory House",
            hospital=self.hospital
        )
        self.doctor = Doctor.objects.create(
            user=self.doc_user,
            name=self.doc_user.name,
            email=self.doc_user.email
        )
        
        self.patient_user = WebUser.objects.create_user(
            email="patient@test.com",
            password="testpassword123",
            usertype="patient",
            name="John Doe",
            hospital=self.hospital
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            name=self.patient_user.name,
            email=self.patient_user.email
        )

        # Create doctor schedule session
        self.schedule = Schedule.objects.create(
            doctor=self.doctor,
            title="General Checkup",
            schedule_date=date(2026, 6, 10),
            schedule_time="10:00:00",
            max_patients=10
        )

    def test_book_appointment_creates_paid_opd_invoice(self):
        # Verify no invoices exist initially
        self.assertEqual(Invoice.objects.count(), 0)

        # Book the appointment
        appointment = AppointmentService.book_appointment(self.patient, self.schedule.id)

        # Verify appointment is booked
        self.assertIsNotNone(appointment)
        self.assertEqual(appointment.appointment_number, 1)
        self.assertEqual(appointment.patient, self.patient)
        self.assertEqual(appointment.schedule, self.schedule)

        # Verify a paid OPD invoice was created
        self.assertEqual(Invoice.objects.count(), 1)
        invoice = Invoice.objects.first()
        self.assertEqual(invoice.patient, self.patient)
        self.assertEqual(invoice.hospital, self.hospital)
        self.assertEqual(invoice.billing_type, 'opd')
        self.assertEqual(invoice.status, 'paid')
        self.assertEqual(float(invoice.total_amount), 500.00)

        # Verify the invoice item details
        self.assertEqual(invoice.items.count(), 1)
        item = invoice.items.first()
        self.assertEqual(item.name, f"OPD Consultation - Dr. {self.doctor.name} ({self.schedule.title})")
        self.assertEqual(item.quantity, 1)
        self.assertEqual(float(item.unit_price), 500.00)

