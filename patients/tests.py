from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Patient


class PatientTests(APITestCase):
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
        self.list_url = '/api/patients/'
        self.valid_payload = {
            'name': 'John Doe',
            'age': 35,
            'gender': 'male',
            'phone': '+919876543210',
            'address': '123 Main St',
            'medical_history': 'Hypertension',
        }

    def test_unauthenticated_request_returns_401(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_patient_returns_201_and_sets_created_by(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.list_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'John Doe')
        self.assertEqual(response.data['created_by'], self.user.id)

        patient = Patient.objects.get(id=response.data['id'])
        self.assertEqual(patient.created_by, self.user)

    def test_list_shows_only_own_patients(self):
        Patient.objects.create(name='Own Patient', age=30, gender='female', created_by=self.user)
        Patient.objects.create(name='Other Patient', age=40, gender='male', created_by=self.other_user)

        self.client.force_authenticate(self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Own Patient')

    def test_retrieve_own_and_other_users_patient(self):
        own_patient = Patient.objects.create(
            name='Own Patient', age=30, gender='female', created_by=self.user
        )
        other_patient = Patient.objects.create(
            name='Other Patient', age=40, gender='male', created_by=self.other_user
        )

        self.client.force_authenticate(self.user)
        own_res = self.client.get(f'{self.list_url}{own_patient.id}/')
        self.assertEqual(own_res.status_code, status.HTTP_200_OK)
        self.assertEqual(own_res.data['name'], 'Own Patient')

        other_res = self.client.get(f'{self.list_url}{other_patient.id}/')
        self.assertEqual(other_res.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_and_patch_update_patient(self):
        patient = Patient.objects.create(
            name='Old Name', age=25, gender='male', created_by=self.user
        )
        detail_url = f'{self.list_url}{patient.id}/'
        self.client.force_authenticate(self.user)

        put_payload = {
            'name': 'Updated Name',
            'age': 26,
            'gender': 'male',
            'phone': '9876543210',
            'address': 'New Address',
            'medical_history': 'None',
        }
        put_res = self.client.put(detail_url, put_payload, format='json')
        self.assertEqual(put_res.status_code, status.HTTP_200_OK)
        self.assertEqual(put_res.data['name'], 'Updated Name')
        self.assertEqual(put_res.data['age'], 26)

        patch_res = self.client.patch(detail_url, {'age': 27}, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data['age'], 27)

    def test_delete_own_and_other_users_patient(self):
        own_patient = Patient.objects.create(
            name='Own Patient', age=30, gender='female', created_by=self.user
        )
        other_patient = Patient.objects.create(
            name='Other Patient', age=40, gender='male', created_by=self.other_user
        )

        self.client.force_authenticate(self.user)
        del_other = self.client.delete(f'{self.list_url}{other_patient.id}/')
        self.assertEqual(del_other.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Patient.objects.filter(id=other_patient.id).exists())

        del_own = self.client.delete(f'{self.list_url}{own_patient.id}/')
        self.assertEqual(del_own.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Patient.objects.filter(id=own_patient.id).exists())

    def test_invalid_age_phone_and_missing_name_return_400(self):
        self.client.force_authenticate(self.user)

        invalid_age = {**self.valid_payload, 'age': 200}
        res_age = self.client.post(self.list_url, invalid_age, format='json')
        self.assertEqual(res_age.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('age', res_age.data)

        invalid_phone = {**self.valid_payload, 'phone': '123-abc'}
        res_phone = self.client.post(self.list_url, invalid_phone, format='json')
        self.assertEqual(res_phone.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone', res_phone.data)

        missing_name = {**self.valid_payload, 'name': '   '}
        res_name = self.client.post(self.list_url, missing_name, format='json')
        self.assertEqual(res_name.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', res_name.data)
