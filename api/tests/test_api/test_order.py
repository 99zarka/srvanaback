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

class OrderAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usertype, created = UserType.objects.get_or_create(user_type_id=1, user_type_name="Customer")
        self.register_url = '/api/register/'

        # Register a user and get tokens
        self.user_data = {
            "email": "orderuser@example.com",
            "username": "orderuser",
            "password": "orderpassword123",
            "password2": "orderpassword123",
            "first_name": "Order",
            "last_name": "User",
            "phone_number": "6666666666",
            "address": "6 Order St",
            # user_type is now optional and defaults to 1 in the model
        }
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.access_token = response.data['tokens']['access']

        # Authenticate the client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

        # Create UserTypes
        self.client_usertype, created = UserType.objects.get_or_create(user_type_id=1, user_type_name="Customer")
        self.tech_usertype, created = UserType.objects.get_or_create(user_type_name="Technician")

        # Create Users
        self.client_user = User.objects.create(
            first_name="Client", last_name="User",
            email="clientuser@example.com", password="clientpassword",
            registration_date=timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0)), phone_number="3344556677", username="clientuser"
        )
        self.technician_user = User.objects.create(
            user_type=self.tech_usertype, first_name="Order", last_name="Tech",
            email="ordertech@example.com", password="ordertechpassword",
            registration_date=timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0)), phone_number="4455667788", username="ordertech"
        )

        # Create ServiceCategory and Service
        self.category = ServiceCategory.objects.create(category_name="OrderTestCategory", description="Category for order test")
        self.service = Service.objects.create(
            category=self.category, service_name="OrderTestService", description="Service for order test",
            service_type="Repair", base_inspection_fee=60.00
        )

        self.order_data = {
            "client_user": self.client_user.user_id,
            "service": self.service.service_id,
            "technician_user": self.technician_user.user_id,
            "order_type": "Emergency",
            "problem_description": "Leaky faucet in kitchen.",
            "requested_location": "123 Main St, Anytown",
            "scheduled_date": "2025-02-01",
            "scheduled_time_start": "10:00",
            "scheduled_time_end": "12:00",
            "order_status": "pending", # Changed to lowercase to match choices
            "creation_timestamp": "2025-01-30",
        }
        self.updated_order_data = {
            "client_user": self.client_user.user_id,
            "service": self.service.service_id,
            "technician_user": self.technician_user.user_id,
            "order_type": "Scheduled",
            "problem_description": "Fixed leaky faucet in kitchen.",
            "requested_location": "123 Main St, Anytown",
            "scheduled_date": "2025-02-01",
            "scheduled_time_start": "10:00",
            "scheduled_time_end": "12:00",
            "order_status": "completed", # Changed to lowercase to match choices
            "creation_timestamp": "2025-01-30",
        }
    def test_create_order_authenticated(self):
        response = self.client.post('/api/orders/', self.order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.get().problem_description, 'Leaky faucet in kitchen.')

    def test_create_order_unauthenticated(self):
        self.client.credentials() # Clear credentials
        response = self.client.post('/api/orders/', self.order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_orders_authenticated(self):
        Order.objects.create(
            client_user=self.client_user, service=self.service, technician_user=self.technician_user,
            order_type="Scheduled", problem_description="Another order", requested_location="456 Oak Ave",
            scheduled_date="2025-03-01", scheduled_time_start="09:00", scheduled_time_end="11:00",
            order_status="Pending", creation_timestamp="2025-02-28"
        )
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_single_order_authenticated(self):
        order = Order.objects.create(
            client_user=self.client_user, service=self.service, technician_user=self.technician_user,
            order_type="Emergency", problem_description="Single order", requested_location="789 Pine St",
            scheduled_date="2025-04-01", scheduled_time_start="13:00", scheduled_time_end="15:00",
            order_status="Pending", creation_timestamp="2025-03-30"
        )
        response = self.client.get(f'/api/orders/{order.order_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['problem_description'], 'Single order')

    def test_update_order_authenticated(self):
        order = Order.objects.create(
            client_user=self.client_user, service=self.service, technician_user=self.technician_user,
            order_type="Emergency", problem_description="Original order", requested_location="101 Elm St",
            scheduled_date="2025-05-01", scheduled_time_start="08:00", scheduled_time_end="10:00",
            order_status="Pending", creation_timestamp="2025-04-30"
        )
        response = self.client.put(f'/api/orders/{order.order_id}/', self.updated_order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'completed')

    def test_delete_order_authenticated(self):
        order = Order.objects.create(
            client_user=self.client_user, service=self.service, technician_user=self.technician_user,
            order_type="Scheduled", problem_description="Order to delete", requested_location="202 Birch Ln",
            scheduled_date="2025-06-01", scheduled_time_start="14:00", scheduled_time_end="16:00",
            order_status="Pending", creation_timestamp="2025-05-30"
        )
        response = self.client.delete(f'/api/orders/{order.order_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Order.objects.count(), 0)
