from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from users.models import User, UserType
from orders.models import Order
from services.models import Service, ServiceCategory
from transactions.models import Transaction
from decimal import Decimal
from datetime import date

class CommissionLogicTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Setup Users
        self.client_type, _ = UserType.objects.get_or_create(user_type_name='client')
        self.tech_type, _ = UserType.objects.get_or_create(user_type_name='technician')
        
        self.client_user = User.objects.create_user(
            email='client@example.com', password='password', user_type=self.client_type,
            first_name='Client', last_name='Test', phone_number='01011111111'
        )
        self.technician_user = User.objects.create_user(
            email='tech@example.com', password='password', user_type=self.tech_type,
            first_name='Tech', last_name='Test', phone_number='01022222222'
        )
        
        # Setup Service
        self.category = ServiceCategory.objects.create(category_name='Test Category', description='Test')
        self.service = Service.objects.create(
            service_name='Test Service', 
            category=self.category, 
            service_type='repair',
            base_inspection_fee=100
        )
        
        # Setup Order
        self.order = Order.objects.create(
            client_user=self.client_user,
            technician_user=self.technician_user,
            service=self.service,
            order_type='direct_hire',
            problem_description='Test',
            requested_location='Test',
            scheduled_date=date.today(),
            scheduled_time_start='10:00',
            scheduled_time_end='12:00',
            order_status='AWAITING_RELEASE',
            final_price=Decimal('1000.00')
        )
        
        # Fund Escrow
        self.client_user.in_escrow_balance = Decimal('1000.00')
        self.client_user.save()
        
        self.url = reverse('orders:order-release-funds', args=[self.order.order_id])
        self.client.force_authenticate(user=self.client_user)

    def test_release_funds_deducts_commission(self):
        """
        Test that release_funds deducts 5% commission and accurately splits transactions.
        """
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh Data
        self.client_user.refresh_from_db()
        self.technician_user.refresh_from_db()
        self.order.refresh_from_db()
        
        # 1. Verify Client Balances
        self.assertEqual(self.client_user.in_escrow_balance, Decimal('0.00')) # Drained
        
        # 2. Verify Technician Payout (1000 * 0.95 = 950)
        expected_payout = Decimal('950.00')
        self.assertEqual(self.technician_user.pending_balance, expected_payout)
        
        # 3. Verify Order Commission Fields
        self.assertEqual(self.order.platform_commission_amount, Decimal('50.00'))
        self.assertEqual(self.order.commission_percentage, Decimal('5.00'))
        self.assertEqual(self.order.amount_to_technician, expected_payout)
        self.assertEqual(self.order.order_status, 'COMPLETED')
        
        # 4. Verify Ledger (Transactions)
        # Payout Transaction
        payout_tx = Transaction.objects.filter(
            order=self.order, transaction_type='PAYOUT'
        ).first()
        self.assertIsNotNone(payout_tx)
        self.assertEqual(payout_tx.amount, expected_payout)
        self.assertEqual(payout_tx.destination_user, self.technician_user)
        
        # Platform Fee Transaction
        fee_tx = Transaction.objects.filter(
            order=self.order, transaction_type='PLATFORM_FEE'
        ).first()
        self.assertIsNotNone(fee_tx)
        self.assertEqual(fee_tx.amount, Decimal('50.00'))
        self.assertIsNone(fee_tx.destination_user)
