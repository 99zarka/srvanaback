from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from users.models import User, UserType
from transactions.models import Transaction
from payments.models import PaymentMethod # Import PaymentMethod
from django.db import transaction as db_transaction
from technicians.models import VerificationDocument # Added for technician verification documents
from services.models import Service, ServiceCategory # Added for Service and ServiceCategory
from django.utils import timezone # Import timezone for PaymentMethod creation

class PaymentViewsTest(APITestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.technician_api = APIClient()
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
            user_type_name='client', # Pass user_type_name string
            available_balance=100.00 # Initial balance
        )
        self.technician_user = User.objects.create_user(
            email='tech@example.com',
            password='password123',
            first_name='Tech',
            last_name='User',
            user_type_name='technician', # Pass user_type_name string
            available_balance=50.00
        )
        # Create a verification document for the technician
        VerificationDocument.objects.create(
            technician_user=self.technician_user,
            document_type='ID Card',
            document_url='http://example.com/id_tech.jpg',
            upload_date=timezone.now().date(),
            verification_status='Approved'
        )

        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='password123',
            first_name='Admin',
            last_name='User',
            user_type_name='admin', # Pass user_type_name string
            is_staff=True,
            is_superuser=True
        )

        # Authenticate clients
        self.client_api.force_authenticate(user=self.client_user)
        self.technician_api.force_authenticate(user=self.technician_user)
        self.admin_api.force_authenticate(user=self.admin_user)

        # Create a ServiceCategory
        self.service_category = ServiceCategory.objects.create(
            category_name='Home Services',
            description='Various services for home maintenance'
        )
        # Create a Service (not directly used in payment tests, but needed for consistency if other models require it)
        self.service = Service.objects.create(
            category=self.service_category,
            service_name='Plumbing',
            description='Professional plumbing services',
            service_type='hourly',
            base_inspection_fee=25.00,
            estimated_price_range_min=80.00,
            estimated_price_range_max=150.00
        )

        # Create a PaymentMethod for the client user
        self.client_payment_method = PaymentMethod.objects.create(
            user=self.client_user,
            card_type='Visa',
            last_four_digits='1111',
            expiration_date='12/2025',
            card_holder_name='Client User',
            is_default=True
        )

        # URLs
        self.deposit_url = reverse('payment-deposit')
        self.withdraw_url = reverse('payment-withdraw')

    def test_deposit_success(self):
        """
        Ensure a user can successfully deposit funds.
        """
        initial_balance = self.client_user.available_balance
        deposit_amount = 50.00
        data = {'amount': deposit_amount, 'payment_method_id': self.client_payment_method.id} # Added payment_method_id
        response = self.client_api.post(self.deposit_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check response contains updated balances
        self.assertIn('available_balance', response.data)
        self.assertIn('in_escrow_balance', response.data)
        self.assertIn('pending_balance', response.data)

        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.available_balance, initial_balance + deposit_amount)
        self.assertTrue(Transaction.objects.filter(
            source_user=self.client_user,
            destination_user=self.client_user,
            transaction_type='DEPOSIT',
            amount=deposit_amount,
            payment_method=self.client_payment_method, # Check payment_method
        ).exists())

    def test_deposit_invalid_amount(self):
        """
        Ensure deposit fails with invalid amounts.
        """
        initial_balance = self.client_user.available_balance
        data_negative = {'amount': -10.00, 'payment_method_id': self.client_payment_method.id}
        response_negative = self.client_api.post(self.deposit_url, data_negative, format='json')
        self.assertEqual(response_negative.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response_negative.data) # Check for 'amount' field error

        data_zero = {'amount': 0.00, 'payment_method_id': self.client_payment_method.id}
        response_zero = self.client_api.post(self.deposit_url, data_zero, format='json')
        self.assertEqual(response_zero.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response_zero.data) # Check for 'amount' field error

        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.available_balance, initial_balance) # Balance should not change
        self.assertFalse(Transaction.objects.filter(transaction_type='DEPOSIT').exists()) # Use 'DEPOSIT' constant

    def test_withdraw_success(self):
        """
        Ensure a user can successfully withdraw funds with sufficient balance.
        """
        initial_balance = self.client_user.available_balance
        withdraw_amount = 50.00
        data = {'amount': withdraw_amount, 'payment_method_id': self.client_payment_method.id} # Added payment_method_id
        response = self.client_api.post(self.withdraw_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check response contains updated balances
        self.assertIn('available_balance', response.data)
        self.assertIn('in_escrow_balance', response.data)
        self.assertIn('pending_balance', response.data)

        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.available_balance, initial_balance - withdraw_amount)
        self.assertTrue(Transaction.objects.filter(
            source_user=self.client_user,
            destination_user=self.client_user,
            transaction_type='WITHDRAWAL',
            amount=withdraw_amount,
            payment_method=self.client_payment_method, # Check payment_method
        ).exists())

    def test_withdraw_insufficient_funds(self):
        """
        Ensure withdrawal fails with insufficient balance.
        """
        initial_balance = self.client_user.available_balance
        withdraw_amount = 200.00 # More than initial balance
        data = {'amount': withdraw_amount, 'payment_method_id': self.client_payment_method.id}
        response = self.client_api.post(self.withdraw_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Adjusted assertion to check the 'amount' field directly
        self.assertIn('Insufficient available balance for withdrawal.', response.data['amount'])

        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.available_balance, initial_balance) # Balance should not change
        self.assertFalse(Transaction.objects.filter(transaction_type='WITHDRAWAL').exists()) # Use 'WITHDRAWAL' constant

    def test_withdraw_invalid_amount(self):
        """
        Ensure withdrawal fails with invalid amounts.
        """
        initial_balance = self.client_user.available_balance
        data_negative = {'amount': -10.00, 'payment_method_id': self.client_payment_method.id}
        response_negative = self.client_api.post(self.withdraw_url, data_negative, format='json')
        self.assertEqual(response_negative.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response_negative.data) # Check for 'amount' field error

        data_zero = {'amount': 0.00, 'payment_method_id': self.client_payment_method.id}
        response_zero = self.client_api.post(self.withdraw_url, data_zero, format='json')
        self.assertEqual(response_zero.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response_zero.data) # Check for 'amount' field error

        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.available_balance, initial_balance) # Balance should not change
        self.assertFalse(Transaction.objects.filter(transaction_type='WITHDRAWAL').exists()) # Use 'WITHDRAWAL' constant

    def test_deposit_unauthenticated(self):
        """
        Ensure unauthenticated users cannot deposit.
        """
        client = APIClient() # Unauthenticated client
        data = {'amount': 10.00, 'payment_method_id': self.client_payment_method.id}
        response = client.post(self.deposit_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_withdraw_unauthenticated(self):
        """
        Ensure unauthenticated users cannot withdraw.
        """
        client = APIClient() # Unauthenticated client
        data = {'amount': 10.00, 'payment_method_id': self.client_payment_method.id}
        response = client.post(self.withdraw_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
