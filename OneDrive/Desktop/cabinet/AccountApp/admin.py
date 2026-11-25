from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Doctor, Patient, Specialty, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'license_number', 'phone')
    search_fields = ('username', 'last_name', 'license_number')
    filter_horizontal = ('specialties',)

    def get_readonly_fields(self, request, obj=None):
        # license_number non modifiable après la création
        if obj:
            return ('license_number',)
        return ()


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'national_id', 'phone', 'birth_date')
    search_fields = ('username', 'last_name', 'national_id')

    def get_readonly_fields(self, request, obj=None):
        # national_id non modifiable après la création
        if obj:
            return ('national_id',)
        return ()
