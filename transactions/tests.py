from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from .models import Transaction
from users.models import User, UserType
from orders.models import Order
from services.models import Service, ServiceCategory
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

class TransactionTests(APITestCase):
    def setUp(self):
        self.client_usertype = UserType.objects.create(user_type_name='client')
        self.technician_usertype = UserType.objects.create(user_type_name='technician')
        self.admin_usertype = UserType.objects.create(user_type_name='admin')

        self.client_user = User.objects.create_user(
            username='clientuser',
            email='client@example.com',
            password='password123',
            user_type_name=self.client_usertype.user_type_name
        )
        self.other_client_user = User.objects.create_user(
            username='otherclient',
            email='other@example.com',
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
            user_type_name=self.admin_usertype.user_type_name,
        )

        self.service_category = ServiceCategory.objects.create(category_name='Electronics Repair')
        self.service = Service.objects.create(
            category=self.service_category,
            service_name='Test Service',
            description='Description for test service',
            service_type='Repair',
            base_inspection_fee=50.00
        )
        self.order = Order.objects.create(
            client_user=self.client_user,
            technician_user=self.technician_user,
            service=self.service,
            order_type='Repair',
            problem_description='Fix something',
            requested_location='Someplace',
            scheduled_date='2025-01-01',
            scheduled_time_start='09:00',
            scheduled_time_end='10:00',
            order_status='completed',
            creation_timestamp='2025-01-01'
        )
        self.other_order = Order.objects.create(
            client_user=self.other_client_user,
            service=self.service,
            order_type='Repair',
            problem_description='Fix something else',
            requested_location='Another Place',
            scheduled_date='2025-01-02',
            scheduled_time_start='11:00',
            scheduled_time_end='12:00',
            order_status='completed',
            creation_timestamp='2025-01-02'
        )

        self.transaction = Transaction.objects.create(
            user=self.client_user,
            order=self.order,
            amount=100.00,
            transaction_type='payment',
            status='completed'
        )
        self.other_transaction = Transaction.objects.create(
            user=self.other_client_user,
            order=self.other_order,
            amount=150.00,
            transaction_type='payment',
            status='completed'
        )

        self.transaction_data = {
            'user': self.client_user.user_id,
            'order': self.order.order_id,
            'amount': 200.00,
            'transaction_type': 'payment',
            'status': 'pending'
        }

        self.list_url = reverse('transaction-list')
        self.detail_url = reverse('transaction-detail', args=[self.transaction.id])
        self.other_detail_url = reverse('transaction-detail', args=[self.other_transaction.id])

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    def test_create_transaction_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, self.transaction_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_transaction_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.post(self.list_url, self.transaction_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 3)

    def test_create_transaction_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.list_url, self.transaction_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_transactions_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_transactions_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only own transactions

    def test_list_transactions_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Admin sees all

    def test_retrieve_transaction_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_own_transaction_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['amount']), 100.00)

    def test_retrieve_other_transaction_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_transaction_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_transaction_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.patch(self.detail_url, {'status': 'failed'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_own_transaction_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.patch(self.detail_url, {'status': 'cancelled'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.status, 'cancelled')

    def test_update_other_transaction_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.patch(self.other_detail_url, {'status': 'failed'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_transaction_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.patch(self.detail_url, {'status': 'failed'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.status, 'failed')

    def test_delete_transaction_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_own_transaction_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Transaction.objects.filter(pk=self.transaction.pk).exists())

    def test_delete_other_transaction_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_transaction_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Transaction.objects.filter(pk=self.transaction.pk).exists())
