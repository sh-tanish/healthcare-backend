from django.contrib import admin
from .models import Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'specialization',
        'email',
        'phone',
        'experience_years',
        'created_by',
        'created_at',
    ]
