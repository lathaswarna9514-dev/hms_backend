import os
import sys
import django
import random
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

# Append apps folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hospitals.models import Hospital
from departments.models import Department
from rooms_beds.models import Room, Bed
from lab.models import LabTest
from pharmacy.models import MedicineCategory, Medicine

def seed_data():
    print("Starting database seeding...")

    # 1. Get or create Hospital
    hospital = Hospital.objects.first()
    if not hospital:
        hospital = Hospital.objects.create(
            name="Apollo City Hospital",
            address="123 Main Street",
            email="contact@apollo.com",
            phone="9876543210"
        )
        print(f"Created default hospital: {hospital.name}")
    else:
        print(f"Using existing hospital: {hospital.name}")

    # 2. Departments (20)
    print("Seeding Departments...")
    department_names = [
        "Cardiology", "Neurology", "Pediatrics", "Orthopedics", "Oncology",
        "Gastroenterology", "Dermatology", "Psychiatry", "Endocrinology", "Rheumatology",
        "Nephrology", "Urology", "Pulmonology", "Ophthalmology", "ENT",
        "General Surgery", "Internal Medicine", "Emergency Medicine", "Radiology", "Pathology",
        "Obstetrics and Gynecology", "Anesthesiology", "Dentistry", "Dietetics"
    ]
    
    departments_created = 0
    for name in department_names[:20]:
        dep, created = Department.objects.get_or_create(
            hospital=hospital,
            name=name,
            defaults={"description": f"{name} department of the hospital."}
        )
        if created:
            departments_created += 1
    print(f"Created {departments_created} new departments.")

    # 3. Rooms and Beds (10 Rooms, 100 Beds)
    print("Seeding Rooms and Beds...")
    room_types = ['general-ward', 'icu', 'private', 'semi-private']
    rooms_created = 0
    beds_created = 0
    
    # Generate unique room numbers by checking max
    existing_rooms = Room.objects.filter(hospital=hospital).count()
    
    for i in range(existing_rooms + 1, existing_rooms + 11):
        room_number = f"R-{100 + i}"
        room_type = random.choice(room_types)
        charges = random.randint(1000, 5000)
        
        room, created = Room.objects.get_or_create(
            hospital=hospital,
            room_number=room_number,
            defaults={
                "room_type": room_type,
                "charges_per_day": charges
            }
        )
        if created:
            rooms_created += 1
            
        # Create 10 beds for each room
        for j in range(1, 11):
            bed_number = f"{room_number}-B{j}"
            status = random.choices(['available', 'occupied', 'maintenance'], weights=[0.7, 0.2, 0.1])[0]
            
            bed, b_created = Bed.objects.get_or_create(
                room=room,
                bed_number=bed_number,
                defaults={"status": status}
            )
            if b_created:
                beds_created += 1

    print(f"Created {rooms_created} new rooms and {beds_created} new beds.")

    # 4. Lab Tests (100)
    print("Seeding Lab Tests...")
    sample_types = ['Blood', 'Urine', 'Saliva', 'Stool', 'Swab', 'Sputum', 'Tissue']
    tests_created = 0
    
    existing_tests = LabTest.objects.filter(hospital=hospital).count()
    
    for i in range(existing_tests + 1, existing_tests + 101):
        test_code = f"TEST-{1000 + i}"
        test_name = f"General Health Panel Test {i}"
        
        # Adding some realistic test names for variety
        realistic_tests = ["Complete Blood Count (CBC)", "Lipid Panel", "Liver Function Test (LFT)", "Thyroid Stimulating Hormone (TSH)", "Urinalysis", "Hemoglobin A1c", "Comprehensive Metabolic Panel (CMP)", "Prothrombin Time (PT)", "Basic Metabolic Panel", "C-Reactive Protein (CRP)"]
        if i <= len(realistic_tests):
            test_name = realistic_tests[i-1]
            test_code = ''.join([c for c in test_name if c.isupper()]) or test_code
            # Append a number if it already exists to avoid unique constraint issues
            test_code = f"{test_code}-{i}"
            
        sample = random.choice(sample_types)
        cost = random.randint(200, 3000)
        
        test, created = LabTest.objects.get_or_create(
            hospital=hospital,
            test_code=test_code,
            defaults={
                "name": test_name,
                "description": f"Detailed {test_name} analysis.",
                "sample_type": sample,
                "reference_range": "Normal range varies by age and gender. Typical: 10-50 units.",
                "cost": cost,
                "is_active": True
            }
        )
        if created:
            tests_created += 1
            
    print(f"Created {tests_created} new lab tests.")

    # 5. Pharma Categories and Products
    print("Seeding Medicine Categories and Products...")
    categories = ["Painkillers", "Antibiotics", "Vitamins", "Antipyretics", "Antihistamines", "Antidiabetics", "Cardiovascular", "Gastrointestinal", "Dermatologicals", "Respiratory"]
    cat_objects = []
    
    for cat_name in categories:
        cat, _ = MedicineCategory.objects.get_or_create(
            name=cat_name,
            defaults={"description": f"Category for {cat_name} medicines."}
        )
        cat_objects.append(cat)
        
    units = ['tablet', 'capsule', 'syrup', 'injection', 'cream', 'drops', 'sachet', 'inhaler']
    manufacturers = ["Pfizer", "Novartis", "Roche", "Merck", "Johnson & Johnson", "Sanofi", "GlaxoSmithKline", "AstraZeneca", "Abbott", "Teva"]
    
    medicines_created = 0
    now = timezone.now()
    
    existing_meds = Medicine.objects.filter(hospital=hospital).count()
    
    for i in range(existing_meds + 1, existing_meds + 201):
        category = random.choice(cat_objects)
        manufacturer = random.choice(manufacturers)
        unit = random.choice(units)
        
        name = f"PharmaMed {i} ({category.name})"
        generic_name = f"Generic Component {i}"
        unit_price = Decimal(random.uniform(5.0, 500.0)).quantize(Decimal('0.00'))
        stock = random.randint(10, 1000)
        reorder = random.randint(5, 50)
        expiry = (now + timedelta(days=random.randint(30, 1000))).date()
        
        med, created = Medicine.objects.get_or_create(
            hospital=hospital,
            name=name,
            defaults={
                "category": category,
                "generic_name": generic_name,
                "manufacturer": manufacturer,
                "unit": unit,
                "unit_price": unit_price,
                "stock_quantity": stock,
                "reorder_level": reorder,
                "expiry_date": expiry,
                "is_active": True
            }
        )
        if created:
            medicines_created += 1
            
    print(f"Created {len(categories)} categories and {medicines_created} new medicines.")
    print("Seeding completed successfully.")

if __name__ == '__main__':
    seed_data()
