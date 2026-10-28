import re
from rest_framework import serializers
from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            'id',
            'name',
            'age',
            'gender',
            'phone',
            'address',
            'medical_history',
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

    def validate_age(self, value):
        if value < 0 or value > 150:
            raise serializers.ValidationError("Age must be between 0 and 150.")
        return value

    def validate_phone(self, value):
        value = value.strip()
        if value and not re.fullmatch(r'^\+?\d{10,15}$', value):
            raise serializers.ValidationError(
                "Phone number must contain 10 to 15 digits and an optional leading '+'."
            )
        return value

