from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.conf import settings
from unittest.mock import patch, MagicMock
from decimal import Decimal
from users.models import User, UserType
from transactions.models import Transaction
from payments.models import PaymentMethod
import hmac
import hashlib

@override_settings(PAYMOB_IFRAME_ID='456', PAYMOB_HMAC_SECRET='mysecret', PAYMOB_API_KEY='key', PAYMOB_INTEGRATION_ID='123')
class PaymobFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_type, _ = UserType.objects.get_or_create(user_type_name='client')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User',
            user_type=self.user_type,
            phone_number='01000000000'
        )
        self.client.force_authenticate(user=self.user)
        self.deposit_url = reverse('payment-deposit')
        self.webhook_url = reverse('payment-webhook') 

    @patch('srvana.paymob_utils.requests.post')
    @override_settings(PAYMOB_IFRAME_ID='456', PAYMOB_HMAC_SECRET='mysecret')
    def test_deposit_initiation_success(self, mock_post):
        """
        Test that calling deposit endpoint initiates Paymob flow and returns URL.
        """
        # Mock Auth Token Response
        mock_auth_resp = MagicMock()
        mock_auth_resp.json.return_value = {"token": "fake_auth_token"}
        mock_auth_resp.status_code = 200
        
        # Mock Register Order Response
        mock_order_resp = MagicMock()
        mock_order_resp.json.return_value = {"id": 12345}
        mock_order_resp.status_code = 201
        
        # Mock Key Request Response
        mock_key_resp = MagicMock()
        mock_key_resp.json.return_value = {"token": "fake_payment_key"}
        mock_key_resp.status_code = 201

        # Configure side_effect to return these mocks in order
        mock_post.side_effect = [mock_auth_resp, mock_order_resp, mock_key_resp]

        # Patch environment variables
        with patch.dict('os.environ', {'PAYMOB_API_KEY': 'key', 'PAYMOB_INTEGRATION_ID': '123', 'PAYMOB_IFRAME_ID': '456'}):
            response = self.client.post(self.deposit_url, {'amount': 100})
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('iframe_url', response.data)
            self.assertIn('fake_payment_key', response.data['iframe_url'])
            
            # Verify internal transaction created
            trans = Transaction.objects.filter(source_user=self.user, transaction_type='DEPOSIT').first()
            self.assertIsNotNone(trans)
            self.assertEqual(trans.status, 'PENDING')
            self.assertEqual(trans.external_id, '12345') # Matches mock_order_resp id

    def test_webhook_success_hmac_valid(self):
        """
        Test that a valid webhook POST updates the balance and transaction status.
        """
        # Create a pending transaction first to be updated
        trans = Transaction.objects.create(
            source_user=self.user,
            transaction_type='DEPOSIT',
            amount=Decimal('500.00'),
            external_id='998877', # External Paymob Order ID
            status='PENDING'
        )

        with patch.dict('os.environ', {'PAYMOB_HMAC_SECRET': 'mysecret'}):
            # Construct HMAC
            # Order of keys matters: amount_cents, created_at, currency, error_occured, has_parent_transaction, id, integration_id, is_3d_secure, is_auth, is_capture, is_refunded, is_standalone_payment, is_voided, order, owner, pending, source_data.pan, source_data.sub_type, source_data.type, success
            # We must replicate simple logic: concatenation.
            # Let's simplify and test the view logic which calls validate_hmac.
            # We can mock validate_hmac to return True to focus on business logic here.
            
            with patch('payments.views.validate_hmac', return_value=True):
                 data = {
                     'type': 'TRANSACTION',
                     'obj': {
                         'success': 'true',
                         'order': {'id': 998877}, # Paymob Order ID nested
                         'amount_cents': 50000
                     },
                     'hmac': 'ignored_due_to_mock' 
                 }
                 
                 # Paymob usually sends data as query params for GET hooks or JSON for POST
                 # Our view handles GET params (standard Django QueryDict from request.GET)
                 # Wait, my view implementation implementation says:
                 # request_data = request.GET.dict() if request.method == 'GET' else request.GET.dict()
                 # and validates request.GET.
                 # So I should send data as query params.
                 
                 params = {
                     'success': 'true',
                     'order': '998877', # Flat ID as usually seen in GET params
                     'amount_cents': '50000',
                     'hmac': 'fake_valid_hmac'
                 }
                 
                 response = self.client.get(self.webhook_url, params)
                 
                 self.assertEqual(response.status_code, status.HTTP_200_OK)
                 
                 # Verify Effect
                 trans.refresh_from_db()
                 self.user.refresh_from_db()
                 
                 self.assertEqual(trans.status, 'COMPLETED')
                 self.assertEqual(self.user.available_balance, Decimal('500.00'))

    def test_webhook_security_hmac_invalid(self):
        """
        Test that an invalid HMAC leads to 403 Forbidden.
        """
        with patch('payments.views.validate_hmac', return_value=False):
            response = self.client.get(self.webhook_url, {'hmac': 'invalid'})
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_webhook_idempotency(self):
        """
        Test that processing the same transaction twice does not double-credit.
        """
        trans = Transaction.objects.create(
            source_user=self.user,
            transaction_type='DEPOSIT',
            amount=Decimal('100.00'),
            external_id='111222',
            status='COMPLETED' # Already completed
        )
        
        initial_balance = self.user.available_balance

        with patch('payments.views.validate_hmac', return_value=True):
             params = {
                 'success': 'true',
                 'order': '111222',
                 'hmac': 'valid'
             }
             response = self.client.get(self.webhook_url, params)
             
             self.assertEqual(response.status_code, status.HTTP_200_OK)
             
             self.user.refresh_from_db()
             # Balance should NOT have changed
             self.assertEqual(self.user.available_balance, initial_balance)
