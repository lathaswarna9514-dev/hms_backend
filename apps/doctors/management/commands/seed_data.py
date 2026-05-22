import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from authentication.models import WebUser
from doctors.models import Doctor, Specialty
from patients.models import Patient
from schedules.models import Schedule
from appointments.models import Appointment

class Command(BaseCommand):
    help = 'Seeds specialties, sample admin, doctor, patient, schedules, and appointments.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        
        specialties_list = [
            (1, 'Accident and emergency medicine'),
            (2, 'Allergology'),
            (3, 'Anaesthetics'),
            (4, 'Biological hematology'),
            (5, 'Cardiology'),
            (6, 'Child psychiatry'),
            (7, 'Clinical biology'),
            (8, 'Clinical chemistry'),
            (9, 'Clinical neurophysiology'),
            (10, 'Clinical radiology'),
            (11, 'Dental, oral and maxillo-facial surgery'),
            (12, 'Dermato-venerology'),
            (13, 'Dermatology'),
            (14, 'Endocrinology'),
            (15, 'Gastro-enterologic surgery'),
            (16, 'Gastroenterology'),
            (17, 'General hematology'),
            (18, 'General Practice'),
            (19, 'General surgery'),
            (20, 'Geriatrics'),
            (21, 'Immunology'),
            (22, 'Infectious diseases'),
            (23, 'Internal medicine'),
            (24, 'Laboratory medicine'),
            (25, 'Maxillo-facial surgery'),
            (26, 'Microbiology'),
            (27, 'Nephrology'),
            (28, 'Neuro-psychiatry'),
            (29, 'Neurology'),
            (30, 'Neurosurgery'),
            (31, 'Nuclear medicine'),
            (32, 'Obstetrics and gynecology'),
            (33, 'Occupational medicine'),
            (34, 'Ophthalmology'),
            (35, 'Orthopaedics'),
            (36, 'Otorhinolaryngology'),
            (37, 'Paediatric surgery'),
            (38, 'Paediatrics'),
            (39, 'Pathology'),
            (40, 'Pharmacology'),
            (41, 'Physical medicine and rehabilitation'),
            (42, 'Plastic surgery'),
            (43, 'Podiatric Medicine'),
            (44, 'Podiatric Surgery'),
            (45, 'Psychiatry'),
            (46, 'Public health and Preventive Medicine'),
            (47, 'Radiology'),
            (48, 'Radiotherapy'),
            (49, 'Respiratory medicine'),
            (50, 'Rheumatology'),
            (51, 'Stomatology'),
            (52, 'Thoracic surgery'),
            (53, 'Tropical medicine'),
            (54, 'Urology'),
            (55, 'Vascular surgery'),
            (56, 'Venereology')
        ]

        with transaction.atomic():
            # 1. Create Specialties
            for sp_id, name in specialties_list:
                Specialty.objects.get_or_create(id=sp_id, defaults={'name': name})
            self.stdout.write(self.style.SUCCESS(f'Seeded {len(specialties_list)} specialties.'))

            # 2. Create Admin
            admin_email = 'admin@edoc.com'
            admin_user, created = WebUser.objects.get_or_create(
                email=admin_email,
                defaults={
                    'usertype': 'a',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            if created:
                admin_user.set_password('123')
                admin_user.save()
                self.stdout.write(self.style.SUCCESS(f'Created Admin user: {admin_email} / 123'))
            else:
                self.stdout.write(f'Admin user {admin_email} already exists.')

            # 3. Create Doctor specialty & profile
            doc_email = 'doctor@edoc.com'
            doc_user, created = WebUser.objects.get_or_create(
                email=doc_email,
                defaults={'usertype': 'd'}
            )
            if created:
                doc_user.set_password('123')
                doc_user.save()
                
            specialty_ae = Specialty.objects.get(id=1)
            doctor, created = Doctor.objects.get_or_create(
                email=doc_email,
                defaults={
                    'user': doc_user,
                    'name': 'Test Doctor',
                    'nic': '000000000',
                    'telephone': '0110000000',
                    'specialty': specialty_ae
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created Doctor: {doc_email} / 123'))
            else:
                self.stdout.write(f'Doctor {doc_email} already exists.')

            # 4. Create Patients
            patient_data = [
                ('patient@edoc.com', 'Test Patient', 'Sri Lanka', '0000000000', '2000-01-01', '0120000000'),
                ('emhashenudara@gmail.com', 'Hashen Udara', 'Sri Lanka', '0110000000', '2022-06-03', '0700000000')
            ]

            for email, name, address, nic, dob_str, tel in patient_data:
                p_user, created = WebUser.objects.get_or_create(
                    email=email,
                    defaults={'usertype': 'p'}
                )
                if created:
                    p_user.set_password('123')
                    p_user.save()

                dob = datetime.datetime.strptime(dob_str, '%Y-%m-%d').date()
                patient, created = Patient.objects.get_or_create(
                    email=email,
                    defaults={
                        'user': p_user,
                        'name': name,
                        'address': address,
                        'nic': nic,
                        'dob': dob,
                        'telephone': tel
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created Patient: {email} / 123'))

            # 5. Create Schedules
            schedules_data = [
                (1, 'Test Session', '2050-01-01', '18:00:00', 50),
                (2, 'Morning Consult', '2026-06-10', '09:00:00', 10),
                (3, 'Cardio Clinic', '2026-06-12', '14:00:00', 15)
            ]

            for sch_id, title, date_str, time_str, max_p in schedules_data:
                sch_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                sch_time = datetime.datetime.strptime(time_str, '%H:%M:%S').time()
                schedule, created = Schedule.objects.get_or_create(
                    id=sch_id,
                    defaults={
                        'doctor': doctor,
                        'title': title,
                        'schedule_date': sch_date,
                        'schedule_time': sch_time,
                        'max_patients': max_p
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created Schedule: {title} on {date_str}'))

            # 6. Create Appointments
            appt_patient = Patient.objects.get(email='patient@edoc.com')
            appt_schedule = Schedule.objects.get(id=1)
            appt, created = Appointment.objects.get_or_create(
                id=1,
                defaults={
                    'patient': appt_patient,
                    'schedule': appt_schedule,
                    'appointment_number': 1,
                    'appointment_date': datetime.date(2022, 6, 3)
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS('Created default appointment matching PHP database.'))

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))
