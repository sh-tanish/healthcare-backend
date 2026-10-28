from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Doctor


class DoctorTests(APITestCase):
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
        self.list_url = '/api/doctors/'
        self.valid_payload = {
            'name': 'Dr. Priya Sharma',
            'specialization': 'Cardiology',
            'email': 'priya.sharma@hospital.com',
            'phone': '+919876543210',
            'experience_years': 12,
        }

    def test_unauthenticated_request_returns_401(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_doctor_and_validation_errors(self):
        self.client.force_authenticate(self.user)

        res = self.client.post(self.list_url, self.valid_payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], 'Dr. Priya Sharma')
        self.assertEqual(res.data['created_by'], self.user.id)

        dup_res = self.client.post(self.list_url, self.valid_payload, format='json')
        self.assertEqual(dup_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', dup_res.data)

        bad_phone = {
            **self.valid_payload,
            'email': 'other1@hospital.com',
            'phone': '123-abc',
        }
        phone_res = self.client.post(self.list_url, bad_phone, format='json')
        self.assertEqual(phone_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone', phone_res.data)

        missing_spec = {
            **self.valid_payload,
            'email': 'other2@hospital.com',
            'specialization': '   ',
        }
        spec_res = self.client.post(self.list_url, missing_spec, format='json')
        self.assertEqual(spec_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('specialization', spec_res.data)

    def test_list_returns_all_doctors_from_different_users(self):
        Doctor.objects.create(
            name='Dr. One',
            specialization='Neurology',
            email='dr.one@hospital.com',
            created_by=self.user,
        )
        Doctor.objects.create(
            name='Dr. Two',
            specialization='Orthopedics',
            email='dr.two@hospital.com',
            created_by=self.other_user,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_existing_and_nonexistent_doctor(self):
        doctor = Doctor.objects.create(
            name='Dr. Two',
            specialization='Orthopedics',
            email='dr.two@hospital.com',
            created_by=self.other_user,
        )

        self.client.force_authenticate(self.user)
        res = self.client.get(f'{self.list_url}{doctor.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Dr. Two')

        not_found_res = self.client.get(f'{self.list_url}99999/')
        self.assertEqual(not_found_res.status_code, status.HTTP_404_NOT_FOUND)

    def test_creator_can_put_patch_and_delete(self):
        doctor = Doctor.objects.create(
            name='Dr. One',
            specialization='Neurology',
            email='dr.one@hospital.com',
            experience_years=5,
            created_by=self.user,
        )
        detail_url = f'{self.list_url}{doctor.id}/'
        self.client.force_authenticate(self.user)

        put_payload = {
            'name': 'Dr. One Updated',
            'specialization': 'Neurosurgery',
            'email': 'dr.one@hospital.com',
            'phone': '9876543210',
            'experience_years': 6,
        }
        put_res = self.client.put(detail_url, put_payload, format='json')
        self.assertEqual(put_res.status_code, status.HTTP_200_OK)
        self.assertEqual(put_res.data['name'], 'Dr. One Updated')

        patch_res = self.client.patch(detail_url, {'experience_years': 7}, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data['experience_years'], 7)

        del_res = self.client.delete(detail_url)
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Doctor.objects.filter(id=doctor.id).exists())

    def test_other_user_cannot_put_or_delete_returns_403(self):
        doctor = Doctor.objects.create(
            name='Dr. One',
            specialization='Neurology',
            email='dr.one@hospital.com',
            created_by=self.user,
        )
        detail_url = f'{self.list_url}{doctor.id}/'
        self.client.force_authenticate(self.other_user)

        put_payload = {
            'name': 'Hacked Name',
            'specialization': 'Neurology',
            'email': 'dr.one@hospital.com',
            'experience_years': 1,
        }
        put_res = self.client.put(detail_url, put_payload, format='json')
        self.assertEqual(put_res.status_code, status.HTTP_403_FORBIDDEN)

        del_res = self.client.delete(detail_url)
        self.assertEqual(del_res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Doctor.objects.filter(id=doctor.id).exists())
