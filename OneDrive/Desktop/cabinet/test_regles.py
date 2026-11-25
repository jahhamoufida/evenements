"""
Remplit la base avec des données de test et vérifie toutes les règles du TP.
Lancer avec :  uv run python test_regles.py
"""
import datetime
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GestionCabinetMedical.settings')
django.setup()

from django.contrib import admin  # noqa: E402
from django.core.exceptions import ValidationError  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.utils import timezone  # noqa: E402

from AccountApp.models import Doctor, Patient, Specialty  # noqa: E402
from AppointmentApp.models import Appointment, Status  # noqa: E402

ok_count = 0
ko_count = 0


def result(success, message):
    global ok_count, ko_count
    if success:
        ok_count += 1
        print(f"  [OK]   {message}")
    else:
        ko_count += 1
        print(f"  [ECHEC] {message}")


def expect_error(message, obj):
    """La validation (full_clean) doit refuser l'objet."""
    try:
        obj.full_clean()
        result(False, message + " -> aucune erreur levée !")
    except ValidationError as e:
        first = next(iter(e.message_dict.values()))[0] if hasattr(e, 'message_dict') else e.messages[0]
        result(True, f"{message} -> refusé ({first})")


print("\n=== 1. Création des données de test ===")

cardio, _ = Specialty.objects.get_or_create(name='Cardiologie')
pedia, _ = Specialty.objects.get_or_create(name='Pédiatrie')
print("  Spécialités : Cardiologie, Pédiatrie")

doctor = Doctor.objects.filter(username='dr_ali').first()
if not doctor:
    doctor = Doctor(username='dr_ali', first_name='Ali', last_name='Ben Salah',
                    email='ali@cabinet.tn', license_number='123456', phone='22123456')
    doctor.set_password('Doctor2026!')
    doctor.full_clean()
    doctor.save()
doctor.specialties.add(cardio)
print(f"  Médecin : {doctor} (username dr_ali / mot de passe Doctor2026!)")

patient = Patient.objects.filter(username='p_sami').first()
if not patient:
    patient = Patient(username='p_sami', first_name='Sami', last_name='Trabelsi',
                      email='sami@mail.tn', national_id='12345678', phone='98123456',
                      birth_date=datetime.date(2000, 5, 10))
    patient.set_password('Patient2026!')
    patient.full_clean()
    patient.save()
print(f"  Patient : {patient} (username p_sami / mot de passe Patient2026!)")
result(patient.pk == patient.user_ptr_id, "patient.pk == id de son User (héritage multi-tables)")

tomorrow = (timezone.now() + datetime.timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
rdv = Appointment.objects.filter(doctor=doctor, appointment_date=tomorrow).first()
if not rdv:
    rdv = Appointment(doctor=doctor, patient=patient, appointment_date=tomorrow,
                      reason='Consultation de contrôle')
    rdv.full_clean()
    rdv.save()
print(f"  Rendez-vous : {rdv}")
result(rdv.status == Status.PENDING, "status par défaut = PENDING (En attente)")
result(rdv.duration_minutes == 30, "duration_minutes par défaut = 30")
result(rdv.created_at is not None and rdv.updated_at is not None, "created_at / updated_at remplis automatiquement")

print("\n=== 2. Vérification des règles ===")

base = dict(username='test_x', password='x', phone='12345678')

expect_error("Doctor : license_number de 5 caractères",
             Doctor(**base, license_number='12345'))
expect_error("Doctor : license_number déjà utilisé",
             Doctor(**base, license_number='123456'))
expect_error("Patient : CIN de 7 chiffres",
             Patient(**{**base, 'phone': '12345678'}, national_id='1234567',
                     birth_date=datetime.date(2000, 1, 1)))
expect_error("Patient : CIN déjà utilisée",
             Patient(**base, national_id='12345678', birth_date=datetime.date(2000, 1, 1)))
expect_error("Patient : téléphone avec des lettres",
             Patient(username='test_x', password='x', phone='12ab5678',
                     national_id='87654321', birth_date=datetime.date(2000, 1, 1)))
expect_error("Patient : date de naissance dans le futur",
             Patient(**base, national_id='87654321',
                     birth_date=timezone.localdate() + datetime.timedelta(days=1)))
expect_error("Appointment : date dans le passé",
             Appointment(doctor=doctor, patient=patient, reason='x',
                         appointment_date=timezone.now() - datetime.timedelta(days=1)))
expect_error("Appointment : même médecin, même date",
             Appointment(doctor=doctor, patient=patient, reason='x', appointment_date=tomorrow))
expect_error("Appointment : ordonnance qui n'est pas un PDF",
             Appointment(doctor=doctor, patient=patient, reason='x',
                         appointment_date=tomorrow + datetime.timedelta(hours=1),
                         prescription=SimpleUploadedFile('ordonnance.txt', b'test')))

# Un rendez-vous passé doit rester modifiable (ex. ajouter l'ordonnance)
past_date = timezone.now() - datetime.timedelta(days=2)
Appointment.objects.filter(doctor=doctor, reason='RDV passé (test)').delete()
old = Appointment.objects.create(doctor=doctor, patient=patient, reason='RDV passé (test)',
                                 appointment_date=past_date)
old.status = Status.CONFIRMED
try:
    old.full_clean()
    result(True, "Un rendez-vous passé reste modifiable (statut changé sans erreur)")
except ValidationError as e:
    result(False, f"Un rendez-vous passé devrait rester modifiable : {e}")
old.delete()

# Identifiants métier non modifiables dans l'admin
doc_admin = admin.site._registry[Doctor]
pat_admin = admin.site._registry[Patient]
result('license_number' in doc_admin.get_readonly_fields(None, doctor),
       "Admin : license_number en lecture seule après création")
result('national_id' in pat_admin.get_readonly_fields(None, patient),
       "Admin : national_id en lecture seule après création")

print(f"\n=== Résultat : {ok_count} OK, {ko_count} échec(s) ===\n")
