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

class TechnicianAvailabilityAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usertype, created = UserType.objects.get_or_create(user_type_id=1, user_type_name="Customer")
        self.register_url = '/api/register/'

        # Register a user and get tokens
        self.user_data = {
            "email": "availuser@example.com",
            "username": "availuser",
            "password": "availpassword123",
            "password2": "availpassword123",
            "first_name": "Avail",
            "last_name": "User",
            "phone_number": "3333333333",
            "address": "3 Avail St",
            # user_type is now optional and defaults to 1 in the model
        }
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.access_token = response.data['tokens']['access']

        # Authenticate the client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

        self.technician_user = User.objects.create(
            first_name="Tech", last_name="User", email="techuser@example.com",
            password="techpassword123", registration_date=timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0)), phone_number="1122334455",
            username="techuser"
        )
        self.availability_data = {
            "technician_user": self.technician_user.user_id,
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "17:00",
            "is_available": True
        }
        self.updated_availability_data = {
            "technician_user": self.technician_user.user_id,
            "day_of_week": "Tuesday",
            "start_time": "10:00",
            "end_time": "18:00",
            "is_available": False
        }

    def test_create_technicianavailability_authenticated(self):
        response = self.client.post('/api/technicianavailabilities/', self.availability_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TechnicianAvailability.objects.count(), 1)
        self.assertEqual(TechnicianAvailability.objects.get().day_of_week, 'Monday')

    def test_create_technicianavailability_unauthenticated(self):
        self.client.credentials() # Clear credentials
        response = self.client.post('/api/technicianavailabilities/', self.availability_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_technicianavailabilities_authenticated(self):
        TechnicianAvailability.objects.create(
            technician_user=self.technician_user, day_of_week="Wednesday",
            start_time="08:00", end_time="16:00", is_available=True
        )
        response = self.client.get('/api/technicianavailabilities/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_single_technicianavailability_authenticated(self):
        availability = TechnicianAvailability.objects.create(
            technician_user=self.technician_user, day_of_week="Thursday",
            start_time="11:00", end_time="19:00", is_available=True
        )
        response = self.client.get(f'/api/technicianavailabilities/{availability.availability_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['day_of_week'], 'Thursday')

    def test_update_technicianavailability_authenticated(self):
        availability = TechnicianAvailability.objects.create(
            technician_user=self.technician_user, day_of_week="Friday",
            start_time="12:00", end_time="20:00", is_available=True
        )
        response = self.client.put(f'/api/technicianavailabilities/{availability.availability_id}/', self.updated_availability_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        availability.refresh_from_db()
        self.assertEqual(availability.day_of_week, 'Tuesday')

    def test_delete_technicianavailability_authenticated(self):
        availability = TechnicianAvailability.objects.create(
            technician_user=self.technician_user, day_of_week="Saturday",
            start_time="09:00", end_time="17:00", is_available=True
        )
        response = self.client.delete(f'/api/technicianavailabilities/{availability.availability_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TechnicianAvailability.objects.count(), 0)
