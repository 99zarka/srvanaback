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

class ServiceAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usertype, created = UserType.objects.get_or_create(user_type_id=1, user_type_name="Customer")
        self.register_url = '/api/register/'

        # Register a user and get tokens
        self.user_data = {
            "email": "serviceuser@example.com",
            "username": "serviceuser",
            "password": "servicepassword123",
            "password2": "servicepassword123",
            "first_name": "Service",
            "last_name": "User",
            "phone_number": "2222222222",
            "address": "2 Service St",
            # user_type is now optional and defaults to 1 in the model
        }
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.access_token = response.data['tokens']['access']

        # Authenticate the client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

        self.category = ServiceCategory.objects.create(category_name="TestCategoryForService", description="Temp category")
        self.service_data = {
            "category": self.category.category_id,
            "service_name": "TestService",
            "description": "Description for TestService",
            "service_type": "Repair",
            "base_inspection_fee": 50.00,
            "estimated_price_range_min": 100.00,
            "estimated_price_range_max": 500.00,
            "emergency_surcharge_percentage": 10.00
        }
        self.updated_service_data = {
            "category": self.category.category_id,
            "service_name": "UpdatedTestService",
            "description": "Updated description for TestService",
            "service_type": "Maintenance",
            "base_inspection_fee": 75.00,
            "estimated_price_range_min": 150.00,
            "estimated_price_range_max": 600.00,
            "emergency_surcharge_percentage": 15.00
        }

    def test_create_service_authenticated(self):
        response = self.client.post('/api/services/', self.service_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Service.objects.count(), 1)
        self.assertEqual(Service.objects.get().service_name, 'TestService')

    def test_create_service_unauthenticated(self):
        self.client.credentials() # Clear credentials
        response = self.client.post('/api/services/', self.service_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_services_authenticated(self):
        Service.objects.create(
            category=self.category, service_name="AnotherService", description="Desc",
            service_type="Installation", base_inspection_fee=30.00
        )
        response = self.client.get('/api/services/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_single_service_authenticated(self):
        service = Service.objects.create(
            category=self.category, service_name="SingleService", description="Desc",
            service_type="Repair", base_inspection_fee=60.00
        )
        response = self.client.get(f'/api/services/{service.service_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['service_name'], 'SingleService')

    def test_update_service_authenticated(self):
        service = Service.objects.create(
            category=self.category, service_name="OriginalService", description="Desc",
            service_type="Repair", base_inspection_fee=40.00
        )
        response = self.client.put(f'/api/services/{service.service_id}/', self.updated_service_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        service.refresh_from_db()
        self.assertEqual(service.service_name, 'UpdatedTestService')

    def test_delete_service_authenticated(self):
        service = Service.objects.create(
            category=self.category, service_name="ServiceToDelete", description="Desc",
            service_type="Repair", base_inspection_fee=70.00
        )
        response = self.client.delete(f'/api/services/{service.service_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Service.objects.count(), 0)
