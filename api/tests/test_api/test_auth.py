from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, datetime
from django.utils import timezone
from api.models import (
    UserType, User, ServiceCategory, Service, Order,
    TechnicianSkill, TechnicianAvailability, VerificationDocument
)
from rest_framework_simplejwt.tokens import RefreshToken

class AuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Ensure UserType with ID 1 exists for default user_type
        self.usertype, created = UserType.objects.get_or_create(user_type_id=1, user_type_name="Customer")
        self.register_url = '/api/register/'
        self.login_url = '/api/login/'

        self.user_data = {
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "testpassword123",
            "password2": "testpassword123",
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "1234567890",
            "address": "123 Test St",
            # user_type is now optional and defaults to 1 in the model
        }

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'testuser@example.com')

    def test_user_registration_mismatched_passwords(self):
        data = self.user_data.copy()
        data['password2'] = 'mismatchedpassword'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_user_registration_existing_email(self):
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_user_login(self):
        self.client.post(self.register_url, self.user_data, format='json')
        login_data = {
            "email": "testuser@example.com",
            "password": "testpassword123"
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_login_invalid_credentials(self):
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
