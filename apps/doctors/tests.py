from django.test import TestCase
from django.utils import timezone
from datetime import datetime, date

from authentication.models import WebUser
from hospitals.models import Hospital
from patients.models import Patient
from doctors.models import Doctor, LeaveRequest
from schedules.models import Schedule
from opd.models import Prescription
from pharmacy.models import Medicine, MedicineCategory, DispenseOrder
from lab.models import LabTest, LabRequest
from common.models import Attendance

class HospitalSystemWorkflowsTestCase(TestCase):
    def setUp(self):
        # Create a mock hospital
        self.hospital = Hospital.objects.create(
            name="Test General Hospital",
            address="123 Health Ave"
        )
        
        # Create user accounts for doctor
        self.doc_user = WebUser.objects.create_user(
            email="doc@test.com",
            password="testpassword123",
            usertype="doctor",
            name="Gregory House",
            hospital=self.hospital
        )
        
        # Create Specialty & Doctor profile
        self.doctor = Doctor.objects.create(
            user=self.doc_user,
            name=self.doc_user.name,
            email=self.doc_user.email
        )
        
        # Create patient
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

    def test_leave_request_available_slots_reduction(self):
        # Create schedule session
        schedule_date = date(2026, 6, 1)
        schedule = Schedule.objects.create(
            doctor=self.doctor,
            title="Morning Consultations",
            schedule_date=schedule_date,
            schedule_time="09:00:00",
            max_patients=15
        )
        
        # Verify initial slots
        self.assertEqual(schedule.available_slots, 15)
        
        # Create APPROVED leave request covering the schedule date
        LeaveRequest.objects.create(
            doctor=self.doctor,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 3),
            reason="Medical conference",
            status="APPROVED"
        )
        
        # Verify available slots reduced to 0
        self.assertEqual(schedule.available_slots, 0)

    def test_absent_attendance_available_slots_reduction(self):
        schedule_date = date(2026, 6, 5)
        schedule = Schedule.objects.create(
            doctor=self.doctor,
            title="Afternoon Consultations",
            schedule_date=schedule_date,
            schedule_time="14:00:00",
            max_patients=10
        )
        
        # Verify initial slots
        self.assertEqual(schedule.available_slots, 10)
        
        # Mark doctor ABSENT on that date
        Attendance.objects.create(
            user=self.doc_user,
            date=schedule_date,
            status="ABSENT"
        )
        
        # Verify available slots reduced to 0
        self.assertEqual(schedule.available_slots, 0)

    def test_prescription_triggers_dispense_order_and_lab_request(self):
        # Set up category and medicine
        category = MedicineCategory.objects.create(name="Analgesic")
        medicine = Medicine.objects.create(
            hospital=self.hospital,
            category=category,
            name="Aspirin 100mg",
            unit="tablet",
            unit_price=0.50,
            stock_quantity=100
        )
        
        # Set up lab test
        lab_test = LabTest.objects.create(
            hospital=self.hospital,
            name="Complete Blood Count",
            test_code="CBC",
            reference_range="4.5-11.0 k/uL",
            cost=20.00
        )
        
        # Create Prescription
        prescription = Prescription.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            diagnosis="Mild headache",
            symptoms="Headache for 2 days",
            medicines=[
                {"medicine_id": medicine.id, "name": medicine.name, "quantity": 10, "instructions": "1-0-1 after food"}
            ],
            suggested_tests=[
                {"test_id": lab_test.id, "name": lab_test.name}
            ]
        )
        
        # Verify pharmacy DispenseOrder is triggered
        dispense_order = DispenseOrder.objects.filter(patient_name=self.patient.name, medicine=medicine).first()
        self.assertIsNotNone(dispense_order)
        self.assertEqual(dispense_order.quantity, 10)
        self.assertEqual(dispense_order.status, "pending")
        
        # Verify LabRequest is triggered
        lab_request = LabRequest.objects.filter(patient_name=self.patient.name, test=lab_test).first()
        self.assertIsNotNone(lab_request)
        self.assertEqual(lab_request.status, "pending")

    def test_pharmacy_dispensing_deducts_stock(self):
        category = MedicineCategory.objects.create(name="Antibiotics")
        medicine = Medicine.objects.create(
            hospital=self.hospital,
            category=category,
            name="Amoxicillin 500mg",
            unit="capsule",
            unit_price=1.20,
            stock_quantity=50
        )
        
        # Create dispense order
        order = DispenseOrder.objects.create(
            medicine=medicine,
            patient_name=self.patient.name,
            quantity=15,
            unit_price=medicine.unit_price,
            prescribed_by=self.doctor.name,
            status="pending"
        )
        
        # Call API client or trigger viewset method to dispense
        from rest_framework.test import APIRequestFactory
        from pharmacy.views import DispenseOrderViewSet
        
        factory = APIRequestFactory()
        # Request context
        request = factory.post(f'/api/pharmacy/orders/{order.id}/dispense/')
        request.user = WebUser.objects.create_user(
            email="pharma@test.com",
            password="testpassword123",
            usertype="pharmacy",
            name="Pharma John",
            hospital=self.hospital
        )
        request.hospital = self.hospital
        
        view = DispenseOrderViewSet.as_view({'post': 'dispense'})
        response = view(request, pk=order.id)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        
        # Refresh medicine and order from DB
        medicine.refresh_from_db()
        order.refresh_from_db()
        
        self.assertEqual(medicine.stock_quantity, 35) # 50 - 15 = 35
        self.assertEqual(order.status, "dispensed")
        self.assertIsNotNone(order.dispensed_at)

    def test_attendance_marking_restricted_to_doctor(self):
        # Create non-doctor user (e.g. nurse)
        nurse_user = WebUser.objects.create_user(
            email="nurse@test.com",
            password="testpassword123",
            usertype="nurse",
            name="Nurse Ratched",
            hospital=self.hospital
        )
        
        from rest_framework.test import APIRequestFactory
        from common.views import AttendanceViewSet
        
        factory = APIRequestFactory()
        
        # Attempt to mark attendance for nurse (should fail)
        request = factory.post('/api/common/attendance/', {
            'user': nurse_user.id,
            'status': 'PRESENT',
            'date': '2026-06-01'
        }, format='json')
        request.user = self.doc_user # Admin or another authenticated user
        request.hospital = self.hospital
        
        view = AttendanceViewSet.as_view({'post': 'create'})
        response = view(request)
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])
        self.assertIn("restricted to doctor profiles", response.data['message'])
        
        # Attempt to mark attendance for doctor (should succeed)
        request2 = factory.post('/api/common/attendance/', {
            'user': self.doc_user.id,
            'status': 'PRESENT',
            'date': '2026-06-01'
        }, format='json')
        request2.user = self.doc_user
        request2.hospital = self.hospital
        
        response2 = view(request2)
        self.assertEqual(response2.status_code, 201) # HTTP 201 Created
        self.assertTrue(response2.data['success'])

