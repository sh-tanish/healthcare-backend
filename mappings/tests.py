from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from doctors.models import Doctor
from patients.models import Patient
from .models import PatientDoctorMapping


class MappingTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user1@example.com',
            email='user1@example.com',
            password='Password123!',
            first_name='User One',
        )
        self.other_user = User.objects.create_user(
            username='user2@example.com',
            email='user2@example.com',
            password='Password123!',
            first_name='User Two',
        )
        self.own_patient = Patient.objects.create(
            name='Aarav Mehta',
            age=34,
            gender='male',
            created_by=self.user,
        )
        self.other_patient = Patient.objects.create(
            name='Riya Kapoor',
            age=28,
            gender='female',
            created_by=self.other_user,
        )
        self.doctor1 = Doctor.objects.create(
            name='Dr. Priya Sharma',
            specialization='Cardiology',
            email='priya@hospital.com',
            created_by=self.user,
        )
        self.doctor2 = Doctor.objects.create(
            name='Dr. Vikram Rao',
            specialization='Neurology',
            email='vikram@hospital.com',
            created_by=self.other_user,
        )
        self.list_url = '/api/mappings/'

    def test_unauthenticated_request_returns_401(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assign_doctor_to_own_patient_returns_201(self):
        self.client.force_authenticate(self.user)
        payload = {'patient': self.own_patient.id, 'doctor': self.doctor1.id}

        res = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['patient'], self.own_patient.id)
        self.assertEqual(res.data['doctor'], self.doctor1.id)
        self.assertEqual(res.data['patient_name'], 'Aarav Mehta')
        self.assertEqual(res.data['doctor_name'], 'Dr. Priya Sharma')
        self.assertIn('assigned_at', res.data)

    def test_duplicate_assignment_returns_400(self):
        self.client.force_authenticate(self.user)
        payload = {'patient': self.own_patient.id, 'doctor': self.doctor1.id}

        first_res = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(first_res.status_code, status.HTTP_201_CREATED)

        dup_res = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(dup_res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_assign_to_other_users_patient_or_nonexistent_doctor_returns_400(self):
        self.client.force_authenticate(self.user)

        other_patient_res = self.client.post(
            self.list_url,
            {'patient': self.other_patient.id, 'doctor': self.doctor1.id},
            format='json',
        )
        self.assertEqual(other_patient_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('patient', other_patient_res.data)

        bad_doctor_res = self.client.post(
            self.list_url,
            {'patient': self.own_patient.id, 'doctor': 99999},
            format='json',
        )
        self.assertEqual(bad_doctor_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('doctor', bad_doctor_res.data)

    def test_list_returns_only_mappings_of_own_patients(self):
        own_mapping = PatientDoctorMapping.objects.create(
            patient=self.own_patient, doctor=self.doctor1
        )
        PatientDoctorMapping.objects.create(
            patient=self.other_patient, doctor=self.doctor2
        )

        self.client.force_authenticate(self.user)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], own_mapping.id)

    def test_get_patient_mappings_and_other_users_patient_returns_404(self):
        PatientDoctorMapping.objects.create(patient=self.own_patient, doctor=self.doctor1)
        PatientDoctorMapping.objects.create(patient=self.own_patient, doctor=self.doctor2)

        self.client.force_authenticate(self.user)
        res = self.client.get(f'{self.list_url}{self.own_patient.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['patient_id'], self.own_patient.id)
        self.assertEqual(res.data['patient_name'], self.own_patient.name)
        self.assertEqual(len(res.data['doctors']), 2)

        other_res = self.client.get(f'{self.list_url}{self.other_patient.id}/')
        self.assertEqual(other_res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_mapping_and_other_users_mapping_returns_404(self):
        own_mapping = PatientDoctorMapping.objects.create(
            patient=self.own_patient, doctor=self.doctor1
        )
        other_mapping = PatientDoctorMapping.objects.create(
            patient=self.other_patient, doctor=self.doctor2
        )

        self.client.force_authenticate(self.user)

        other_del = self.client.delete(f'{self.list_url}{other_mapping.id}/')
        self.assertEqual(other_del.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(PatientDoctorMapping.objects.filter(id=other_mapping.id).exists())

        own_del = self.client.delete(f'{self.list_url}{own_mapping.id}/')
        self.assertEqual(own_del.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PatientDoctorMapping.objects.filter(id=own_mapping.id).exists())

    def test_deleting_patient_or_doctor_cascades_mappings(self):
        m1 = PatientDoctorMapping.objects.create(
            patient=self.own_patient, doctor=self.doctor1
        )
        m2 = PatientDoctorMapping.objects.create(
            patient=self.other_patient, doctor=self.doctor2
        )

        self.own_patient.delete()
        self.assertFalse(PatientDoctorMapping.objects.filter(id=m1.id).exists())

        self.doctor2.delete()
        self.assertFalse(PatientDoctorMapping.objects.filter(id=m2.id).exists())
