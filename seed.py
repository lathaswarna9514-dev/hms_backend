import os
import sys

# Append apps folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Set up Django environment
import django
django.setup()

from hospitals.models import Hospital
from authentication.models import WebUser
from doctors.models import Doctor

def seed_db():
    print("Starting database seeding...")

    # Create Hospital
    hospital, created = Hospital.objects.get_or_create(
        email="cityhospital@edochms.com",
        defaults={
            "name": "eDoc City Hospital",
            "phone": "9876543210",
            "address": "123 Health Ave, Medical District",
            "is_active": True
        }
    )
    if created:
        print(f"Created Hospital: {hospital.name}")
    else:
        print(f"Hospital already exists: {hospital.name}")

    from django.conf import settings
    super_admin_email = getattr(settings, 'EMAIL_HOST_USER', 'superadmin@edochms.com')

    # Role Accounts definitions
    users_data = [
        {
            "email": super_admin_email,
            "password": "AdminPassword123",
            "usertype": "super-admin",
            "name": "Global Super Admin",
            "hospital": None
        },
        {
            "email": "hospitaladmin@edochms.com",
            "password": "AdminPassword123",
            "usertype": "hospital-admin",
            "name": "City Admin",
            "hospital": hospital
        },
        {
            "email": "doctor@edochms.com",
            "password": "AdminPassword123",
            "usertype": "doctor",
            "name": "Dr. Sarah Smith",
            "hospital": hospital
        },
        {
            "email": "nurse@edochms.com",
            "password": "AdminPassword123",
            "usertype": "nurse",
            "name": "Nurse Emily Cole",
            "hospital": hospital
        },
        {
            "email": "frontdesk@edochms.com",
            "password": "AdminPassword123",
            "usertype": "frontdesk",
            "name": "Reception Desk A",
            "hospital": hospital
        },
        {
            "email": "pharmacy@edochms.com",
            "password": "AdminPassword123",
            "usertype": "pharmacy",
            "name": "Pharma Dispenser Joe",
            "hospital": hospital
        },
        {
            "email": "lab@edochms.com",
            "password": "AdminPassword123",
            "usertype": "lab",
            "name": "Lab Tech Alan",
            "hospital": hospital
        },
        {
            "email": "patient@edochms.com",
            "password": "AdminPassword123",
            "usertype": "patient",
            "name": "Robert Patient",
            "hospital": hospital
        }
    ]

    for ud in users_data:
        user, created = WebUser.objects.get_or_create(
            email=ud["email"],
            defaults={
                "usertype": ud["usertype"],
                "name": ud["name"],
                "hospital": ud["hospital"],
                "is_active": True
            }
        )
        if created:
            user.set_password(ud["password"])
            user.save()
            print(f"Created {ud['usertype']} account: {ud['email']}")

            # Create Doctor Profile if this is a doctor
            if ud["usertype"] == "doctor":
                Doctor.objects.get_or_create(
                    email=user.email,
                    defaults={
                        "user": user,
                        "name": user.name,
                        "nic": "Not Provided",
                        "telephone": "Not Provided"
                    }
                )
                print(f"Created Doctor Profile for: {user.name}")
        else:
            print(f"Account already exists: {ud['email']}")

    print("Seeding completed successfully.")

if __name__ == "__main__":
    seed_db()
