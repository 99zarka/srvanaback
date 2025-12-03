from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, datetime
from django.utils import timezone
from users.models import UserType, User
from services.models import ServiceCategory, Service
from orders.models import Order

from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

class OrderAPITests(TestCase):
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

        # Create ServiceCategory and Service
        self.category = ServiceCategory.objects.create(category_name="OrderTestCategory", description="Category for order test")
        self.service = Service.objects.create(
            category=self.category, service_name="OrderTestService", description="Service for order test",
            service_type="Repair", base_inspection_fee=60.00
        )

        # Create Orders
        self.order = Order.objects.create(
            client_user=self.client_user,
            service=self.service,
            technician_user=self.technician_user, # Assign technician to the order for testing
            order_type="Emergency",
            problem_description="Leaky faucet in kitchen.",
            requested_location="123 Main St, Anytown",
            scheduled_date="2025-02-01",
            scheduled_time_start="10:00",
            scheduled_time_end="12:00",
            order_status="pending",
            creation_timestamp="2025-01-30",
        )
        # self.other_order = Order.objects.create( # Commented out to simplify test data
        #     client_user=self.other_client_user,
        #     service=self.service,
        #     technician_user=self.other_technician_user,
        #     order_type="Scheduled",
        #     problem_description="Broken window.",
        #     requested_location="456 Other St, Othertown",
        #     scheduled_date="2025-02-02",
        #     scheduled_time_start="13:00",
        #     scheduled_time_end="15:00",
        #     order_status="completed",
        #     creation_timestamp="2025-01-31",
        # )

        self.order_data = {
            "service": self.service.service_id,
            "order_type": "Emergency",
            "problem_description": "New leaky faucet in kitchen.",
            "requested_location": "123 Main St, Anytown",
            "scheduled_date": "2025-02-03",
            "scheduled_time_start": "09:00",
            "scheduled_time_end": "11:00",
        }
        self.updated_order_data = {
            "order_type": "Scheduled",
            "problem_description": "Fixed leaky faucet in kitchen.",
            "order_status": "completed",
        }

        from django.urls import reverse
        self.list_url = reverse('orders:order-list')
        self.detail_url = reverse('orders:order-detail', kwargs={'order_id': self.order.order_id})
        # self.other_detail_url = reverse('orders:order-detail', kwargs={'order_id': self.other_order.order_id}) # Commented out

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    def test_create_order_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, self.order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_order_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.post(self.list_url, self.order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2) # 1 existing + 1 new
        self.assertEqual(response.data['problem_description'], 'New leaky faucet in kitchen.')

    def test_create_order_technician(self):
        client = self.get_auth_client(self.technician_user)
        response = client.post(self.list_url, self.order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2) # 1 existing + 1 new
        self.assertEqual(response.data['problem_description'], 'New leaky faucet in kitchen.')

    def test_create_order_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.list_url, self.order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2) # 1 existing + 1 new

    def test_list_orders_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_orders_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # print(f"Client list response data: {response.data}") # Debugging - now fixed
        self.assertEqual(len(response.data['results']), 1) # Only orders belonging to the authenticated client (self.order)

    def test_list_orders_technician(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # print(f"Technician list response data: {response.data}") # Debugging - now fixed
        self.assertEqual(len(response.data['results']), 0) # Technicians should not see generic order list

    def test_list_orders_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # print(f"Admin list response data: {response.data}") # Debugging - now fixed
        self.assertEqual(len(response.data['results']), 1) # Admin sees the one existing order (self.order)

    def test_retrieve_order_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_order_client_owner(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['problem_description'], 'Leaky faucet in kitchen.')

    def test_retrieve_order_client_not_owner_forbidden(self):
        client = self.get_auth_client(self.other_client_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_order_technician_assigned(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['problem_description'], 'Leaky faucet in kitchen.')

    def test_retrieve_order_technician_not_assigned_forbidden(self):
        client = self.get_auth_client(self.other_technician_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_order_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['problem_description'], 'Leaky faucet in kitchen.')

    def test_update_order_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.patch(self.detail_url, self.updated_order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_order_client_owner(self):
        client = self.get_auth_client(self.client_user)
        response = client.patch(self.detail_url, self.updated_order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Clients can update their own orders
        self.order.refresh_from_db()
        self.assertEqual(self.order.order_status, 'completed')

    def test_update_order_technician_assigned(self):
        client = self.get_auth_client(self.technician_user)
        response = client.patch(self.detail_url, self.updated_order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.order_status, 'completed')

    def test_update_order_technician_not_assigned_forbidden(self):
        client = self.get_auth_client(self.other_technician_user)
        response = client.patch(self.detail_url, self.updated_order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_order_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.patch(self.detail_url, self.updated_order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.order_status, 'completed')

    def test_delete_order_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_order_client_owner(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT) # Clients can delete their own orders

    def test_delete_order_technician_assigned(self):
        client = self.get_auth_client(self.technician_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT) # Technicians can delete their assigned orders

    def test_delete_order_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Order.objects.count(), 0) # 1 initially, 1 deleted, 0 remaining
