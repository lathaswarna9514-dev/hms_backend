import os
import sys

# Append apps folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from doctors.models import Specialty

def seed_specialties():
    specialties_list = [
        "Cardiologist",
        "Dermatologist",
        "Endocrinologist",
        "Gastroenterologist",
        "Hematologist",
        "Infectious Disease Specialist",
        "Nephrologist",
        "Neurologist",
        "Oncologist",
        "Ophthalmologist",
        "Orthopedic Surgeon",
        "Otolaryngologist (ENT)",
        "Pediatrician",
        "Pulmonologist",
        "Psychiatrist",
        "Rheumatologist",
        "Urologist",
        "Anesthesiologist",
        "Radiologist",
        "Pathologist",
        "Obstetrician / Gynecologist",
        "General Surgeon",
        "Cardiothoracic Surgeon",
        "Neurosurgeon",
        "Plastic Surgeon",
        "Pediatric Surgeon",
        "Vascular Surgeon",
        "Allergist / Immunologist",
        "Geriatrician",
        "Emergency Medicine Specialist",
        "Family Medicine Physician",
        "General Practitioner",
        "Sports Medicine Specialist",
        "Physical Medicine & Rehab Specialist",
        "Neonatologist",
        "Pediatric Cardiologist",
        "Pediatric Neurologist",
        "Pediatric Oncologist",
        "Medical Geneticist",
        "Sleep Medicine Specialist"
    ]

    print(f"Checking specialties in database... Total: {Specialty.objects.count()}")
    created_count = 0
    for name in specialties_list:
        obj, created = Specialty.objects.get_or_create(name=name)
        if created:
            created_count += 1
            print(f"Created specialty: {name}")

    print(f"Seeding completed. Added {created_count} new specialties. Total in DB: {Specialty.objects.count()}")

if __name__ == "__main__":
    seed_specialties()
