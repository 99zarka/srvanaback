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

class UserAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usertype, created = UserType.objects.get_or_create(user_type_id=1, user_type_name="Customer")
        self.register_url = '/api/register/'
        self.login_url = '/api/login/'

        # Register a user and get tokens
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
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.access_token = response.data['tokens']['access']
        self.refresh_token = response.data['tokens']['refresh']

        # Authenticate the client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

        self.user = User.objects.get(email="testuser@example.com")
        self.updated_user_data = {
            "user_type": self.usertype.user_type_id, # Keep this for update test, as it might be explicitly set
            "first_name": "Updated",
            "last_name": "User",
            "email": "updateduser@example.com",
            "phone_number": "0987654321",
            "username": "updateduser",
            "registration_date": timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0))
        }

    def test_create_user_unauthenticated(self):
        # Test that unauthenticated users cannot create users directly via UserViewSet
        self.client.credentials() # Clear credentials
        response = self.client.post('/api/users/', self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_users_authenticated(self):
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only the registered user

    def test_get_single_user_authenticated(self):
        response = self.client.get(f'/api/users/{self.user.user_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'testuser@example.com')

    def test_update_user_authenticated(self):
        response = self.client.put(f'/api/users/{self.user.user_id}/', self.updated_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updateduser@example.com')

    def test_delete_user_authenticated(self):
        response = self.client.delete(f'/api/users/{self.user.user_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 0)
