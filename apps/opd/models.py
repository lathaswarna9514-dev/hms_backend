from django.db import models
from patients.models import Patient
from doctors.models import Doctor
from appointments.models import Appointment

class Prescription(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='prescriptions')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='prescriptions')
    diagnosis = models.TextField()
    symptoms = models.TextField()
    
    # JSON list of medicines: [{"medicine_id": 1, "name": "Aspirin", "quantity": 10, "instructions": "1-0-1 after food"}]
    medicines = models.JSONField(default=list, blank=True)
    
    # JSON list of suggested tests: [{"test_id": 1, "name": "CBC"}]
    suggested_tests = models.JSONField(default=list, blank=True)
    
    advice = models.TextField(blank=True, null=True)
    diet_advice = models.TextField(blank=True, null=True)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'prescription'
        ordering = ['-created_at']

    def __str__(self):
        return f"Prescription #{self.id} for {self.patient.name} by Dr. {self.doctor.name}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # 1. Create DispenseOrders for pharmacy
            from pharmacy.models import Medicine, DispenseOrder
            for med_data in self.medicines:
                med_id = med_data.get('medicine_id')
                qty = int(med_data.get('quantity', 1))
                notes = med_data.get('instructions', '')
                
                try:
                    medicine = Medicine.objects.get(id=med_id)
                except (Medicine.DoesNotExist, ValueError, TypeError):
                    # Fallback to lookup by name
                    med_name = med_data.get('name')
                    medicine = Medicine.objects.filter(name__iexact=med_name).first()
                
                if medicine:
                    DispenseOrder.objects.create(
                        medicine=medicine,
                        patient_name=self.patient.name,
                        quantity=qty,
                        unit_price=medicine.unit_price,
                        prescribed_by=self.doctor.name,
                        notes=notes,
                        status='pending'
                    )
            
            # 2. Create LabRequests for laboratories
            from lab.models import LabTest, LabRequest
            for test_data in self.suggested_tests:
                test_id = test_data.get('test_id')
                
                try:
                    lab_test = LabTest.objects.get(id=test_id)
                except (LabTest.DoesNotExist, ValueError, TypeError):
                    # Fallback to lookup by name
                    test_name = test_data.get('name')
                    lab_test = LabTest.objects.filter(name__iexact=test_name).first()
                
                if lab_test:
                    LabRequest.objects.create(
                        hospital=self.doctor.user.hospital if (self.doctor.user and self.doctor.user.hospital) else None,
                        test=lab_test,
                        patient_name=self.patient.name,
                        prescribed_by=self.doctor.name,
                        status='pending'
                    )
