from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'age', 'gender', 'phone', 'created_by', 'created_at']
