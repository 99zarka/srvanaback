from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, datetime
from django.utils import timezone
from users.models import UserType, User
from services.models import ServiceCategory, Service
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse

class ServiceAPITests(TestCase):
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
        self.technician_user = User.objects.create_user(
            username='techuser',
            email='technician@example.com',
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

        self.category = ServiceCategory.objects.create(category_name="TestCategoryForService", description="Temp category")
        self.service = Service.objects.create(
            category=self.category, service_name="TestService", description="Service for TestService",
            service_type="Repair", base_inspection_fee=50.00, estimated_price_range_min=100.00,
            estimated_price_range_max=500.00, emergency_surcharge_percentage=10.00
        )
        self.other_service = Service.objects.create(
            category=self.category, service_name="OtherService", description="Other Service",
            service_type="Installation", base_inspection_fee=30.00, estimated_price_range_min=50.00,
            estimated_price_range_max=200.00, emergency_surcharge_percentage=5.00
        )

        self.service_data = {
            "category": self.category.category_id,
            "service_name": "NewService",
            "description": "Description for NewService",
            "service_type": "Maintenance",
            "base_inspection_fee": 60.00,
            "estimated_price_range_min": 120.00,
            "estimated_price_range_max": 550.00,
            "emergency_surcharge_percentage": 12.00
        }
        self.updated_service_data = {
            "service_name": "UpdatedTestService",
            "description": "Updated description for TestService",
            "service_type": "Maintenance",
            "base_inspection_fee": 75.00,
            "estimated_price_range_min": 150.00,
            "estimated_price_range_max": 600.00,
            "emergency_surcharge_percentage": 15.00
        }

        self.list_url = reverse('service-list')
        self.detail_url = reverse('service-detail', args=[self.service.service_id])
        self.other_detail_url = reverse('service-detail', args=[self.other_service.service_id])

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    # --- Unauthenticated User Tests ---
    def test_unauthenticated_create_service(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, self.service_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_list_services(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Publicly accessible
        self.assertEqual(len(response.data), 2)

    def test_unauthenticated_retrieve_service(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Publicly accessible
        self.assertEqual(response.data['service_name'], 'TestService')

    def test_unauthenticated_update_service(self):
        updated_data = {'service_name': 'Unauthorized Update'}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_delete_service(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Client User Tests ---
    def test_client_create_service_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.post(self.list_url, self.service_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_list_services(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_client_retrieve_service(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['service_name'], 'TestService')

    def test_client_update_service_forbidden(self):
        client = self.get_auth_client(self.client_user)
        updated_data = {'service_name': 'Client Update'}
        response = client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_delete_service_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Technician User Tests ---
    def test_technician_create_service_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.post(self.list_url, self.service_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_technician_list_services(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_technician_retrieve_service(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['service_name'], 'TestService')

    def test_technician_update_service_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        updated_data = {'service_name': 'Technician Update'}
        response = client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_technician_delete_service_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Admin User Tests ---
    def test_admin_create_service(self):
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.list_url, self.service_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Service.objects.count(), 3)
        self.assertEqual(response.data['service_name'], 'NewService')

    def test_admin_list_services(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_admin_retrieve_service(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['service_name'], 'TestService')

    def test_admin_update_service(self):
        client = self.get_auth_client(self.admin_user)
        response = client.patch(self.detail_url, self.updated_service_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.service.refresh_from_db()
        self.assertEqual(self.service.service_name, 'UpdatedTestService')

    def test_admin_delete_service(self):
        client = self.get_auth_client(self.admin_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Service.objects.count(), 1) # One deleted
