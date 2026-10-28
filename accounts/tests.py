from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken


class AuthTests(APITestCase):
    def setUp(self):
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        self.refresh_url = '/api/auth/token/refresh/'
        self.valid_payload = {
            'name': 'Alice Smith',
            'email': 'Alice@Example.com',
            'password': 'StrongPassword123!',
        }

    def test_register_success(self):
        response = self.client.post(self.register_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Alice Smith')
        self.assertEqual(response.data['email'], 'alice@example.com')
        self.assertIn('id', response.data)
        self.assertNotIn('password', response.data)

        user = User.objects.get(email='alice@example.com')
        self.assertEqual(user.username, 'alice@example.com')
        self.assertEqual(user.first_name, 'Alice Smith')
        self.assertNotEqual(user.password, self.valid_payload['password'])
        self.assertTrue(user.check_password(self.valid_payload['password']))

    def test_register_duplicate_email_returns_400(self):
        self.client.post(self.register_url, self.valid_payload, format='json')
        duplicate_payload = {
            'name': 'Another Alice',
            'email': 'ALICE@example.com',
            'password': 'AnotherPassword123!',
        }
        response = self.client.post(self.register_url, duplicate_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_missing_fields_returns_400(self):
        response = self.client.post(self.register_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)

    def test_register_weak_password_returns_400(self):
        weak_payload = {
            'name': 'Bob',
            'email': 'bob@example.com',
            'password': '123',
        }
        response = self.client.post(self.register_url, weak_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_login_success_returns_tokens_and_user(self):
        self.client.post(self.register_url, self.valid_payload, format='json')
        login_payload = {
            'email': 'ALICE@EXAMPLE.COM',
            'password': 'StrongPassword123!',
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'alice@example.com')
        self.assertEqual(response.data['user']['name'], 'Alice Smith')

    def test_login_wrong_password_returns_401(self):
        self.client.post(self.register_url, self.valid_payload, format='json')
        response = self.client.post(
            self.login_url,
            {'email': 'alice@example.com', 'password': 'WrongPassword123!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Invalid email or password.')

    def test_token_refresh_works(self):
        self.client.post(self.register_url, self.valid_payload, format='json')
        login_res = self.client.post(
            self.login_url,
            {'email': 'alice@example.com', 'password': 'StrongPassword123!'},
            format='json',
        )
        refresh_token = login_res.data['refresh']

        refresh_res = self.client.post(
            self.refresh_url,
            {'refresh': refresh_token},
            format='json',
        )
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_res.data)
        self.assertTrue(len(refresh_res.data['access']) > 0)

    def test_access_token_from_login_decodes_to_user(self):
        reg_res = self.client.post(self.register_url, self.valid_payload, format='json')
        login_res = self.client.post(
            self.login_url,
            {'email': 'alice@example.com', 'password': 'StrongPassword123!'},
            format='json',
        )
        access_token_str = login_res.data['access']
        self.assertTrue(len(access_token_str) > 0)

        decoded = AccessToken(access_token_str)
        self.assertEqual(str(decoded['user_id']), str(reg_res.data['id']))
