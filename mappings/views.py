from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from doctors.serializers import DoctorSerializer
from patients.models import Patient
from .models import PatientDoctorMapping
from .serializers import MappingSerializer


class MappingListCreateView(generics.ListCreateAPIView):
    serializer_class = MappingSerializer

    def get_queryset(self):
        return PatientDoctorMapping.objects.filter(
            patient__created_by=self.request.user
        ).select_related('patient', 'doctor')


# Per assignment spec, /api/mappings/<int:pk>/ shares one URL for two lookups:
# GET treats `pk` as a Patient ID (listing doctors assigned to that patient),
# while DELETE treats `pk` as a PatientDoctorMapping ID (removing that assignment).
class MappingDetailView(APIView):
    def get(self, request, pk):
        patient = get_object_or_404(Patient, id=pk, created_by=request.user)
        doctors = [m.doctor for m in patient.mappings.select_related('doctor')]
        return Response({
            'patient_id': patient.id,
            'patient_name': patient.name,
            'doctors': DoctorSerializer(doctors, many=True).data,
        })

    def delete(self, request, pk):
        mapping = get_object_or_404(
            PatientDoctorMapping, id=pk, patient__created_by=request.user
        )
        mapping.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
