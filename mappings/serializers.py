from rest_framework import serializers
from .models import PatientDoctorMapping


class MappingSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source='patient.name')
    doctor_name = serializers.ReadOnlyField(source='doctor.name')

    class Meta:
        model = PatientDoctorMapping
        fields = ['id', 'patient', 'doctor', 'patient_name', 'doctor_name', 'assigned_at']
        read_only_fields = ['id', 'patient_name', 'doctor_name', 'assigned_at']
        validators = []

    def validate(self, attrs):
        request = self.context['request']
        patient = attrs['patient']
        doctor = attrs['doctor']

        if patient.created_by != request.user:
            raise serializers.ValidationError({'patient': 'Patient not found.'})

        if PatientDoctorMapping.objects.filter(patient=patient, doctor=doctor).exists():
            raise serializers.ValidationError('This doctor is already assigned to this patient.')

        return attrs

