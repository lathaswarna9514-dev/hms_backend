import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from authentication.models import WebUser
from doctors.models import Doctor

def fix():
    doctor_users = WebUser.objects.filter(usertype='doctor')
    for user in doctor_users:
        doc, created = Doctor.objects.get_or_create(
            email=user.email,
            defaults={
                "user": user,
                "name": user.name,
                "nic": "Not Provided",
                "telephone": "Not Provided"
            }
        )
        if created:
            print(f"Created Doctor profile for existing user: {user.name}")
        else:
            print(f"Doctor profile already exists for: {user.name}")

if __name__ == "__main__":
    fix()
