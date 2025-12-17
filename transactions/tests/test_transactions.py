from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from users.models import User, UserType
from orders.models import Order
from services.models import Service, ServiceCategory
from transactions.models import Transaction
from disputes.models import Dispute
from django.db import transaction as db_transaction # Import for atomic operations
from datetime import timedelta, datetime
from django.utils import timezone
from decimal import Decimal

class TransactionTests(APITestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.admin_api = APIClient()

        # Create UserTypes
        self.client_user_type = UserType.objects.create(user_type_name='client')
        self.technician_user_type = UserType.objects.create(user_type_name='technician')
        self.admin_user_type = UserType.objects.create(user_type_name='admin')

        # Create Users
        self.client_user = User.objects.create_user(
            email='client@example.com',
            password='password123',
            first_name='Client',
            last_name='User',
            user_type_name='client',
            available_balance=Decimal('1000.00'),
            in_escrow_balance=Decimal('0.00'),
            pending_balance=Decimal('0.00')
        )
        self.technician_user = User.objects.create_user(
            email='tech@example.com',
            password='password123',
            first_name='Tech',
            last_name='User',
            user_type_name='technician',
            available_balance=Decimal('500.00'),
            in_escrow_balance=Decimal('0.00'),
            pending_balance=Decimal('0.00')
        )
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='password123',
            first_name='Admin',
            last_name='User',
            user_type_name='admin',
            is_staff=True,
            is_superuser=True
        )

        # Authenticate clients
        self.client_api.force_authenticate(user=self.client_user)
        self.admin_api.force_authenticate(user=self.admin_user)

        # Create a ServiceCategory
        self.service_category = ServiceCategory.objects.create(
            category_name='Home Services',
            description='Various services for home maintenance'
        )
        # Create a Service
        self.service = Service.objects.create(
            category=self.service_category,
            service_name='Plumbing',
            description='Professional plumbing services',
            service_type='hourly',
            base_inspection_fee=Decimal('25.00'),
            estimated_price_range_min=Decimal('80.00'),
            estimated_price_range_max=Decimal('150.00')
        )

        # Create an Order for testing related transactions
        self.order = Order.objects.create(
            client_user=self.client_user,
            service=self.service,
            order_type='on_demand',
            problem_description='Fix my leaky faucet',
            requested_location='123 Test St',
            scheduled_date=(timezone.now() + timedelta(days=5)).date(),
            scheduled_time_start='09:00',
            scheduled_time_end='17:00',
            order_status='OPEN',
            final_price=Decimal('100.00')
        )

        # Create a Dispute for testing related transactions
        self.dispute = Dispute.objects.create(
            order=self.order,
            initiator=self.client_user,
            client_argument='Technician did not finish the job',
            status='OPEN'
        )

        self.transaction_list_url = reverse('transactions:transaction-list')

    def test_create_deposit_transaction_by_admin(self):
        """
        Admin can create a DEPOSIT transaction.
        """
        data = {
            'source_user': self.client_user.user_id,
            'destination_user': self.client_user.user_id,
            'transaction_type': 'DEPOSIT',
            'amount': '50.00',
            'currency': 'EGP',
            'payment_method': 'Credit Card'
        }
        response = self.admin_api.post(self.transaction_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.transaction_type, 'DEPOSIT')
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.source_user, self.client_user)
        self.assertEqual(transaction.destination_user, self.client_user)

    def test_create_escrow_hold_transaction_by_admin(self):
        """
        Admin can create an ESCROW_HOLD transaction.
        """
        data = {
            'source_user': self.client_user.user_id,
            'destination_user': self.technician_user.user_id,
            'order': self.order.order_id,
            'transaction_type': 'ESCROW_HOLD',
            'amount': '100.00',
            'currency': 'EGP',
            'payment_method': 'Available Balance'
        }
        response = self.admin_api.post(self.transaction_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.transaction_type, 'ESCROW_HOLD')
        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(transaction.source_user, self.client_user)
        self.assertEqual(transaction.destination_user, self.technician_user)
        self.assertEqual(transaction.order, self.order)

    def test_create_dispute_payout_transaction_by_admin(self):
        """
        Admin can create a DISPUTE_PAYOUT transaction.
        """
        data = {
            'source_user': self.client_user.user_id,
            'destination_user': self.technician_user.user_id,
            'order': self.order.order_id,
            'dispute': self.dispute.dispute_id,
            'transaction_type': 'DISPUTE_PAYOUT',
            'amount': '75.00',
            'currency': 'EGP',
            'payment_method': 'Escrow'
        }
        response = self.admin_api.post(self.transaction_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.transaction_type, 'DISPUTE_PAYOUT')
        self.assertEqual(transaction.amount, Decimal('75.00'))
        self.assertEqual(transaction.source_user, self.client_user)
        self.assertEqual(transaction.destination_user, self.technician_user)
        self.assertEqual(transaction.order, self.order)
        self.assertEqual(transaction.dispute, self.dispute)

    def test_list_transactions_by_admin(self):
        """
        Admin can list all transactions.
        """
        Transaction.objects.create(
            source_user=self.client_user,
            destination_user=self.client_user,
            transaction_type='DEPOSIT', amount=Decimal('50.00'))
        Transaction.objects.create(
            source_user=self.client_user,
            destination_user=self.technician_user,
            order=self.order,
            transaction_type='ESCROW_HOLD', amount=Decimal('100.00'))
        
        response = self.admin_api.get(self.transaction_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_list_transactions_by_client_user(self):
        """
        Client user can list their own transactions (as source or destination).
        """
        Transaction.objects.create(
            source_user=self.client_user,
            destination_user=self.client_user,
            transaction_type='DEPOSIT', amount=Decimal('50.00'))
        Transaction.objects.create(
            source_user=self.client_user,
            destination_user=self.technician_user,
            order=self.order,
            transaction_type='ESCROW_HOLD', amount=Decimal('100.00'))
        # Other user's transaction
        Transaction.objects.create(
            source_user=self.technician_user,
            destination_user=self.admin_user,
            transaction_type='WITHDRAWAL', amount=Decimal('20.00'))
        
        response = self.client_api.get(self.transaction_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2) # Should see only own transactions

    def test_retrieve_transaction_by_admin(self):
        """
        Admin can retrieve any transaction.
        """
        transaction = Transaction.objects.create(
            source_user=self.client_user,
            destination_user=self.client_user,
            transaction_type='DEPOSIT', amount=Decimal('50.00'))
        
        url = reverse('transactions:transaction-detail', args=[transaction.transaction_id])
        response = self.admin_api.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['transaction_type'], 'DEPOSIT')

    def test_retrieve_transaction_by_owner(self):
        """
        A user involved in a transaction (source or destination) can retrieve it.
        """
        transaction = Transaction.objects.create(
            source_user=self.client_user,
            destination_user=self.technician_user,
            transaction_type='ESCROW_HOLD', amount=Decimal('100.00'))
        
        url = reverse('transactions:transaction-detail', args=[transaction.transaction_id])
        response = self.client_api.get(url) # Client is source_user
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['transaction_type'], 'ESCROW_HOLD')

        self.client_api.force_authenticate(user=self.technician_user) # Technician is destination_user
        response = self.client_api.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['transaction_type'], 'ESCROW_HOLD')

    def test_retrieve_transaction_unauthorized(self):
        """
        An unauthorized user cannot retrieve a transaction.
        """
        transaction = Transaction.objects.create(
            source_user=self.client_user,
            destination_user=self.client_user,
            transaction_type='DEPOSIT', amount=Decimal('50.00'))
        
        unauth_user = User.objects.create_user(
            email='unauth@example.com',
            password='password123',
            user_type_name='client'
        )
        self.client_api.force_authenticate(user=unauth_user)
        url = reverse('transactions:transaction-detail', args=[transaction.transaction_id])
        response = self.client_api.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_transaction_by_admin(self):
        """
        Admin can update a transaction.
        """
        transaction = Transaction.objects.create(
            source_user=self.client_user,
            destination_user=self.client_user,
            transaction_type='DEPOSIT', amount=Decimal('50.00'))
        
        data = {'amount': '75.00'}
        url = reverse('transactions:transaction-detail', args=[transaction.transaction_id])
        response = self.admin_api.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        transaction.refresh_from_db()
        self.assertEqual(transaction.amount, Decimal('75.00'))

    def test_update_transaction_unauthorized(self):
        """
        Unauthorized users cannot update a transaction.
        """
        transaction = Transaction.objects.create(
            source_user=self.client_user,
            destination_user=self.client_user,
            transaction_type='DEPOSIT', amount=Decimal('50.00'))
        
        data = {'amount': '75.00'}
        url = reverse('transactions:transaction-detail', args=[transaction.transaction_id])
        response = self.client_api.patch(url, data, format='json') # Client tries to update
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        transaction.refresh_from_db()
        self.assertEqual(transaction.amount, Decimal('50.00')) # Amount should not change

    def test_delete_transaction_by_admin(self):
        """
        Admin can delete a transaction.
        """
        transaction = Transaction.objects.create(
            source_user=self.client_user,
            destination_user=self.client_user,
            transaction_type='DEPOSIT', amount=Decimal('50.00'))
        
        url = reverse('transactions:transaction-detail', args=[transaction.transaction_id])
        response = self.admin_api.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Transaction.objects.filter(pk=transaction.pk).exists())

    def test_delete_transaction_unauthorized(self):
        """
        Unauthorized users cannot delete a transaction.
        """
        transaction = Transaction.objects.create(
            source_user=self.client_user,
            destination_user=self.client_user,
            transaction_type='DEPOSIT', amount=Decimal('50.00'))
        
        url = reverse('transactions:transaction-detail', args=[transaction.transaction_id])
        response = self.client_api.delete(url) # Client tries to delete
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Transaction.objects.filter(pk=transaction.pk).exists())
