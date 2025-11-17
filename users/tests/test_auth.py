from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, datetime
from django.utils import timezone
from users.models import UserType, User
from services.models import ServiceCategory, Service
from orders.models import Order
from technicians.models import TechnicianSkill, TechnicianAvailability, VerificationDocument
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

class AuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client_usertype, created = UserType.objects.get_or_create(user_type_id=1, user_type_name="client")
        self.technician_usertype, created = UserType.objects.get_or_create(user_type_id=2, user_type_name="technician")
        self.admin_usertype, created = UserType.objects.get_or_create(user_type_id=3, user_type_name="admin")

        self.register_url = '/api/users/register/'
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
            "user_type_name": self.client_usertype.user_type_name,
        }

        self.admin_user = User.objects.create(
            email="admin@example.com",
            username="adminuser",
            password=make_password("adminpassword123"),
            first_name="Admin",
            last_name="User",
            phone_number="0987654321",
            address="456 Admin Ave",
            user_type=self.admin_usertype,
            is_staff=True,
            is_superuser=True
        )
        self.admin_token = str(RefreshToken.for_user(self.admin_user).access_token)

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(User.objects.get(email='testuser@example.com').email, 'testuser@example.com')

    def test_user_registration_mismatched_passwords(self):
        data = self.user_data.copy()
        data['password2'] = 'mismatchedpassword'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_user_registration_existing_email(self):
        self.client.post(self.register_url, self.user_data, format='json')
        # Attempt to register again with the same email
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_user_login(self):
        # Register a user first
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
