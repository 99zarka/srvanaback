from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import Transaction, User, Order, Service, ServiceCategory
from api.models.users import UserType

class TransactionTests(APITestCase):
    def setUp(self):
        self.usertype_customer = UserType.objects.create(user_type_name='Customer')
        self.usertype_technician = UserType.objects.create(user_type_name='Technician')

        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='password123',
            user_type=self.usertype_customer
        )
        self.technician = User.objects.create_user(
            username='technician',
            email='technician@example.com',
            password='password123',
            user_type=self.usertype_technician
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
            client_user=self.customer,
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
        self.transaction_data = {
            'user': self.customer.pk,
            'order': self.order.order_id,
            'amount': 100.00,
            'transaction_type': 'payment',
            'status': 'completed',
        }
        self.transaction = Transaction.objects.create(
            user=self.technician,
            order=self.order,
            amount=50.00,
            transaction_type='refund',
            status='pending',
        )
        # Create a second transaction for the customer to be listed
        self.transaction2 = Transaction.objects.create(
            user=self.customer,
            order=self.order,
            amount=75.00,
            transaction_type='payment',
            status='completed',
        )
        self.list_url = reverse('transaction-list')
        self.detail_url = reverse('transaction-detail', args=[self.transaction.id])

    def test_create_transaction(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(self.list_url, self.transaction_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 3)
        self.assertEqual(response.data['amount'], '100.00')

    def test_list_transactions(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # All transactions should be visible for an authenticated user

    def test_retrieve_transaction(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], '50.00')

    def test_update_transaction(self):
        self.client.force_authenticate(user=self.technician)
        updated_data = {'status': 'completed'}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.status, 'completed')

    def test_delete_transaction(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Transaction.objects.count(), 1)
