from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, datetime
from django.utils import timezone
from ..models import TechnicianAvailability
from users.models import (
    UserType, User
)
from services.models import ServiceCategory, Service
from orders.models import Order
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse


class TechnicianAvailabilityAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create UserTypes
        self.client_usertype, created = UserType.objects.get_or_create(user_type_name="client")
        self.technician_usertype, created = UserType.objects.get_or_create(user_type_name="technician")
        self.admin_usertype, created = UserType.objects.get_or_create(user_type_name="admin")

        # Create Users
        self.client_user = User.objects.create_user(
            username='clientuser',
            email='client@example.com',
            password='password123',
            user_type_name=self.client_usertype.user_type_name
        )
        self.other_client_user = User.objects.create_user(
            username='otherclient',
            email='otherclient@example.com',
            password='password123',
            user_type_name=self.client_usertype.user_type_name
        )
        self.technician_user = User.objects.create_user(
            username='techuser',
            email='technician@example.com',
            password='password123',
            user_type_name=self.technician_usertype.user_type_name
        )
        self.other_technician_user = User.objects.create_user(
            username='othertech',
            email='othertech@example.com',
            password='password123',
            user_type_name=self.technician_usertype.user_type_name
        )
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            username="adminuser",
            password="adminpassword123",
            first_name="Admin",
            last_name="User",
            phone_number="0987654321",
            address="456 Admin Ave",
            user_type_name=self.admin_usertype.user_type_name,
        )

        self.availability_data = {
            "technician_user": self.technician_user.user_id,
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "17:00",
            "is_available": True
        }
        self.other_availability_data = {
            "technician_user": self.other_technician_user.user_id,
            "day_of_week": "Tuesday",
            "start_time": "10:00",
            "end_time": "18:00",
            "is_available": False
        }
        self.availability = TechnicianAvailability.objects.create(
            technician_user=self.technician_user,
            day_of_week="Monday",
            start_time="09:00",
            end_time="17:00",
            is_available=True
        )
        self.other_availability = TechnicianAvailability.objects.create(
            technician_user=self.other_technician_user,
            day_of_week="Tuesday",
            start_time="10:00",
            end_time="18:00",
            is_available=False
        )

        self.list_url = reverse('technicianavailability-list')
        self.detail_url = reverse('technicianavailability-detail', args=[self.availability.availability_id])
        self.other_detail_url = reverse('technicianavailability-detail', args=[self.other_availability.availability_id])

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    # --- Unauthenticated User Tests ---
    def test_unauthenticated_create_availability(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, self.availability_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_list_availability(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_retrieve_availability(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_update_availability(self):
        updated_data = {'is_available': False}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_delete_availability(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Client User Tests ---
    def test_client_create_availability_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.post(self.list_url, self.availability_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_list_availability(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Client can see all availability

    def test_client_retrieve_availability(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['day_of_week'], 'Monday')

    def test_client_update_availability_forbidden(self):
        client = self.get_auth_client(self.client_user)
        updated_data = {'is_available': False}
        response = client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_delete_availability_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Technician User Tests (Owner) ---
    def test_technician_create_availability(self):
        client = self.get_auth_client(self.technician_user)
        response = client.post(self.list_url, self.availability_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TechnicianAvailability.objects.count(), 3)
        self.assertEqual(response.data['day_of_week'], 'Monday')

    def test_technician_list_own_availability(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Technician sees their own availability
        self.assertEqual(response.data[0]['day_of_week'], 'Monday')

    def test_technician_retrieve_own_availability(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['day_of_week'], 'Monday')

    def test_technician_update_own_availability(self):
        client = self.get_auth_client(self.technician_user)
        updated_data = {'start_time': '10:00', 'end_time': '18:00', 'is_available': False}
        response = client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.availability.refresh_from_db()
        self.assertEqual(self.availability.start_time, '10:00')

    def test_technician_delete_own_availability(self):
        client = self.get_auth_client(self.technician_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TechnicianAvailability.objects.filter(availability_id=self.availability.availability_id).exists(), False)

    # --- Technician User Tests (Non-Owner) ---
    def test_technician_retrieve_other_availability_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Technician cannot retrieve other technician's availability

    def test_technician_update_other_availability_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        updated_data = {'is_available': True}
        response = client.patch(self.other_detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_technician_delete_other_availability_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.delete(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Admin User Tests ---
    def test_admin_create_availability(self):
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.list_url, self.availability_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TechnicianAvailability.objects.count(), 3)

    def test_admin_list_all_availability(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Admin sees all availability

    def test_admin_retrieve_any_availability(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['day_of_week'], 'Monday')

    def test_admin_update_any_availability(self):
        client = self.get_auth_client(self.admin_user)
        updated_data = {'start_time': '11:00', 'end_time': '19:00', 'is_available': False}
        response = client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.availability.refresh_from_db()
        self.assertEqual(self.availability.start_time, '11:00')

    def test_admin_delete_any_availability(self):
        client = self.get_auth_client(self.admin_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TechnicianAvailability.objects.count(), 1) # One deleted
