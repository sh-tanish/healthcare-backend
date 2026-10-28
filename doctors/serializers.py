import re
from rest_framework import serializers
from .models import Doctor


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = [
            'id',
            'name',
            'specialization',
            'email',
            'phone',
            'experience_years',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be blank.")
        return value

    def validate_specialization(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Specialization cannot be blank.")
        return value

    def validate_phone(self, value):
        value = value.strip()
        if value and not re.fullmatch(r'^\+?\d{10,15}$', value):
            raise serializers.ValidationError(
                "Phone number must contain 10 to 15 digits and an optional leading '+'."
            )
        return value

