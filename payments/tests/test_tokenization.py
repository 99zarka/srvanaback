from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from payments.models import PaymentMethod
from users.models import UserType
from transactions.models import Transaction
from unittest.mock import patch, MagicMock
from decimal import Decimal

User = get_user_model()

class PaymobTokenizationTests(APITestCase):

    def setUp(self):
        # Create Users
        self.client_user_type, _ = UserType.objects.get_or_create(user_type_name="client")
        self.technician_user_type, _ = UserType.objects.get_or_create(user_type_name="technician")

        self.user = User.objects.create_user(
            email="client@example.com",
            password="password123",
            first_name="Test",
            last_name="Client",
            phone_number="01012345678",
            user_type=self.client_user_type
        )
        # Ensure wallet exists (if implemented via signals, fine. If not, create explicitly)
        # Assuming User model has fields directly or related wallet. 
        # Based on previous code, user has 'available_balance' directly on model.
        self.user.available_balance = Decimal('0.00')
        self.user.save()

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="password123",
            first_name="Other",
            last_name="User",
            user_type=self.client_user_type
        )

        self.client.force_authenticate(user=self.user)
        
        # URLs
        self.deposit_url = reverse('payment-list') + 'deposit/' # Assuming router generates 'payment-list' and action 'deposit'
        # Adjust URL finding if needed. ViewSet basename='payment'. Action 'deposit' -> /api/payments/deposit/
        # Using reverse might be tricky if basename is set differently. 
        # Based on urls.py: router.register(r'', PaymentViewSet, basename='payment')
        # So 'payment-deposit' might be the name.
        self.deposit_url = '/api/payments/deposit/'
        self.webhook_url = '/api/payments/webhook/'

    @patch('payments.views.validate_hmac')
    def test_webhook_token_event_saves_card(self, mock_validate_hmac):
        """
        Req 1: Test Webhook - TOKEN Event matches user and saves card.
        """
        mock_validate_hmac.return_value = True

        # 1. Setup Request Data
        # We need a Transaction to link the order_id to the User
        txn = Transaction.objects.create(
            source_user=self.user,
            destination_user=self.user,
            transaction_type='DEPOSIT',
            amount=Decimal('100.00'),
            status='PENDING',
            external_id='999888' # Paymob Order ID
        )
        
        payload = {
            "type": "TOKEN",
            "obj": {
                "token": "tkn_123456789",
                "masked_pan": "1234",
                "card_subtype": "Visa",
                "email": "client@example.com",
                "order_id": 999888, # Matches external_id
                "expiry_year": "2026",
                "expiry_month": "12"
            }
        }

        # 2. Call Webhook
        response = self.client.post(self.webhook_url, payload, format='json')

        # 3. Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify PaymentMethod created
        pm = PaymentMethod.objects.filter(user=self.user, masked_pan="1234").first()
        self.assertIsNotNone(pm)
        self.assertEqual(pm.paymob_token, "tkn_123456789")
        self.assertEqual(pm.card_type, "Visa")
        self.assertEqual(pm.expiration_date, "2026/12")

    @patch('payments.views.validate_hmac')
    def test_webhook_transaction_event_updates_balance(self, mock_validate_hmac):
        """
        Req 2: Test Webhook - TRANSACTION Event updates balance & Idempotency.
        """
        mock_validate_hmac.return_value = True

        # Setup Transaction
        txn = Transaction.objects.create(
            source_user=self.user,
            destination_user=self.user,
            transaction_type='DEPOSIT',
            amount=Decimal('500.00'),
            status='PENDING',
            external_id='777666'
        )

        payload = {
            "type": "TRANSACTION",
            "obj": {
                "success": True,
                "order": {"id": 777666},
                "amount_cents": 50000,
                "currency": "EGP",
                "id": 123456 # Paymob Transaction ID
            }
        }

        # 1. First Call (Success)
        response = self.client.post(self.webhook_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        txn.refresh_from_db()
        self.assertEqual(self.user.available_balance, Decimal('500.00'))
        self.assertEqual(txn.status, 'COMPLETED')

        # 2. Idempotency Check (Second Call)
        # Should return 200 but NOT add money again
        response = self.client.post(self.webhook_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.available_balance, Decimal('500.00')) # Unchanged

    @patch('payments.views.get_payment_key')
    @patch('payments.views.register_order')
    @patch('payments.views.get_auth_token')
    def test_deposit_standard_flow(self, mock_auth, mock_register, mock_key):
        """
        Req 3: Test Deposit - Standard Flow (Iframe).
        """
        # Mocks
        mock_auth.return_value = "auth_token_xxx"
        mock_register.return_value = "order_999"
        mock_key.return_value = "pay_key_xxx"

        data = {"amount": 250.0}
        response = self.client.post(self.deposit_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("iframe_url", response.data)
        self.assertIn("payment_token=pay_key_xxx", response.data["iframe_url"])
        
        # Verify transaction created
        self.assertTrue(Transaction.objects.filter(amount=250.0, status='PENDING').exists())

    @patch('payments.views.pay_with_token')
    @patch('payments.views.get_payment_key')
    @patch('payments.views.register_order')
    @patch('payments.views.get_auth_token')
    def test_deposit_saved_card_flow(self, mock_auth, mock_register, mock_key, mock_pay_token):
        """
        Req 4: Test Deposit - Saved Card (Token) Flow.
        """
        # Setup Saved Card
        pm = PaymentMethod.objects.create(
            user=self.user,
            masked_pan="4444",
            card_type="Visa",
            paymob_token="token_secret_123"
        )

        # Mocks
        mock_auth.return_value = "auth_token_xxx"
        mock_register.return_value = "order_888"
        mock_key.return_value = "pay_key_xxx"
        
        # Mock Paymob Pay Response (Success)
        mock_pay_token.return_value = {
            "success": "true",
            "pending": "false"
        }

        data = {
            "amount": 100.0,
            "payment_method_id": pm.id
        }
        
        response = self.client.post(self.deposit_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify pay_with_token was called with correct token
        mock_pay_token.assert_called_with("token_secret_123", "pay_key_xxx")

    @patch('payments.views.pay_with_token')
    @patch('payments.views.get_payment_key')
    @patch('payments.views.register_order')
    @patch('payments.views.get_auth_token')
    def test_deposit_saved_card_3ds_redirect(self, mock_auth, mock_register, mock_key, mock_pay_token):
        """
        Req 4 (cont): Test Deposit - Saved Card with 3D Secure Redirect.
        """
        pm = PaymentMethod.objects.create(
            user=self.user,
            masked_pan="5555",
            card_type="MasterCard",
            paymob_token="token_secret_3ds"
        )
         # Mocks
        mock_auth.return_value = "auth_token_xxx"
        mock_register.return_value = "order_777"
        mock_key.return_value = "pay_key_xxx"

        # Mock Paymob Pay Response (Pending / 3DS)
        mock_pay_token.return_value = {
            "success": "false",
            "pending": "true",
            "redirect_url": "https://paymob.com/3ds-challenge"
        }

        data = {
            "amount": 100.0,
            "payment_method_id": pm.id
        }
        
        response = self.client.post(self.deposit_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("iframe_url", response.data) # We map redirect_url to iframe_url key for frontend consistency
        self.assertEqual(response.data["iframe_url"], "https://paymob.com/3ds-challenge")

    def test_permissions_payment_method_isolation(self):
        """
        Req 5: Ensure users cannot access others' payment methods.
        """
        # Create PM for other user
        other_pm = PaymentMethod.objects.create(
            user=self.other_user,
            masked_pan="9999",
            card_type="Visa",
            paymob_token="other_token"
        )

        # Try to use it as self.user
        mock_auth = MagicMock(return_value="token")
        
        # We need to mock the internals if we hit the view logic, 
        # but here we can rely on the validation error "Invalid payment method"
        # or "does not belong to user" if we implement Object Level Permissions filtering.
        
        # However, calling 'deposit' logic performs `PaymentMethod.objects.get(id=id, user=user)`
        # So it should raise ValidationError inside the view or 404.
        
        # We need to mock the Paymob flows up to the point of PM check
        with patch('payments.views.get_auth_token') as m1, \
             patch('payments.views.register_order') as m2, \
             patch('payments.views.get_payment_key') as m3:
             
             m1.return_value = "x"
             m2.return_value = "y"
             m3.return_value = "z"

             data = {"amount": 100, "payment_method_id": other_pm.id}
             response = self.client.post(self.deposit_url, data)
             
             # Should fail validation
             self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
