from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.utils import timezone


# ---------- Validators ----------

# Téléphone et CIN : exactement 8 chiffres
phone_validator = RegexValidator(
    regex=r'^\d{8}$',
    message="Le numéro de téléphone doit contenir exactement 8 chiffres.",
)

national_id_validator = RegexValidator(
    regex=r'^\d{8}$',
    message="Le numéro de CIN doit contenir exactement 8 chiffres.",
)


def validate_past_date(value):
    """Méthode 1 : la date de naissance doit être antérieure à aujourd'hui."""
    if value >= timezone.localdate():
        raise ValidationError("La date de naissance doit être antérieure à la date du jour.")


# ---------- Modèles ----------

class User(AbstractUser):
    """Modèle utilisateur personnalisé (point d'extension du projet)."""
    pass


class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Specialties"

    def __str__(self):
        return self.name


class Doctor(User):
    # Héritage multi-tables : username, password, email, first_name, last_name viennent de User
    license_number = models.CharField(
        max_length=6,
        unique=True,
        validators=[MinLengthValidator(6)],
    )
    phone = models.CharField(max_length=8, validators=[phone_validator])
    specialties = models.ManyToManyField(Specialty, related_name='doctors', blank=True)

    class Meta:
        verbose_name = "Doctor"

    def __str__(self):
        return f"Dr {self.first_name} {self.last_name}"


class Patient(User):
    national_id = models.CharField(
        max_length=8,
        unique=True,
        validators=[national_id_validator],
    )
    phone = models.CharField(max_length=8, validators=[phone_validator])
    birth_date = models.DateField(validators=[validate_past_date])

    class Meta:
        verbose_name = "Patient"

    def clean(self):
        """Méthode 2 : même contrôle de birth_date dans clean()."""
        super().clean()
        if self.birth_date and self.birth_date >= timezone.localdate():
            raise ValidationError(
                {'birth_date': "La date de naissance doit être antérieure à la date du jour."}
            )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
