from rest_framework.test import APIClient
from django.test import TransactionTestCase # Changed base class for transaction control
from django.core.management import call_command
from django.urls import reverse
from users.models import User, UserType
from orders.models import Order
from services.models import Service, ServiceCategory # Added for Service and ServiceCategory
from transactions.models import Transaction
from notifications.models import Notification
from django.utils import timezone
from datetime import timedelta
from io import StringIO
from decimal import Decimal # Added for precise monetary calculations
import sys
from technicians.models import VerificationDocument # Added for technician verification documents

class AutoReleaseCommandTest(TransactionTestCase): # Changed base class
    def setUp(self):
        super().setUp() # Call super for TransactionTestCase setup
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
            available_balance=Decimal('1000.00'),
            in_escrow_balance=Decimal('0.00')
        )
        self.technician_user = User.objects.create_user(
            email='tech@example.com',
            password='password123',
            first_name='Tech',
            last_name='User',
            user_type_name='technician', # Pass user_type_name string
            available_balance=Decimal('500.00'),
            pending_balance=Decimal('0.00')
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

        # Create a ServiceCategory
        self.service_category = ServiceCategory.objects.create(
            category_name='Home Services',
            description='Various services for home maintenance'
        )
        # Create a Service
        self.service = Service.objects.create(
            category=self.service_category,
            service_name='Gardening',
            description='Garden maintenance',
            service_type='hourly',
            base_inspection_fee=Decimal('15.00'),
            estimated_price_range_min=Decimal('70.00'),
            estimated_price_range_max=Decimal('100.00')
        )

    def _create_order_with_escrow(self, client_user, technician_user, final_price, status='awaiting_release', auto_release_delta=timedelta(days=-1)):
        auto_release_date_val = timezone.now() + auto_release_delta 
        order = Order.objects.create(
            client_user=client_user,
            technician_user=technician_user,
            service=self.service,
            order_type='Repair', # Added required field
            problem_description='Test auto-release order', # Renamed 'description' to 'problem_description'
            requested_location='Test Location', # Added required field
            scheduled_date=timezone.now().date(), # Added required field
            scheduled_time_start='09:00', # Added required field
            scheduled_time_end='17:00', # Added required field
            order_status=status,
            final_price=Decimal(str(final_price)), # Ensure final_price is Decimal
            auto_release_date=auto_release_date_val
        )
        client_user.in_escrow_balance += Decimal(str(final_price)) # Ensure final_price is Decimal
        client_user.save()
        return order

    def test_auto_release_success(self):
        """
        Ensure funds are auto-released for an order past its auto_release_date.
        """
        order = self._create_order_with_escrow(self.client_user, self.technician_user, Decimal('100.00'), status='awaiting_release', auto_release_delta=timedelta(days=-1))
        
        initial_client_escrow = self.client_user.in_escrow_balance
        initial_technician_pending = self.technician_user.pending_balance

        out = StringIO()
        sys.stdout = out # Redirect stdout to capture command output
        call_command('check_auto_release', stdout=out)
        sys.stdout = sys.__stdout__ # Restore stdout

        order.refresh_from_db() # Refresh order to get the latest status
        self.client_user.refresh_from_db()
        self.technician_user.refresh_from_db()

        self.assertEqual(order.order_status, 'completed')
        self.assertTrue(order.job_completion_timestamp is not None)
        self.assertEqual(self.client_user.in_escrow_balance, initial_client_escrow - Decimal('100.00'))
        self.assertEqual(self.technician_user.pending_balance, initial_technician_pending + Decimal('100.00'))

        self.assertTrue(Transaction.objects.filter(
            order=order,
            transaction_type='escrow_release',
            amount=Decimal('100.00'),
            status='completed',
            # description field removed as it does not exist in Transaction model
        ).exists())

        self.assertTrue(Notification.objects.filter(
            user=self.technician_user,
            notification_type='funds_auto_released'
        ).exists())
        self.assertTrue(Notification.objects.filter(
            user=self.client_user,
            notification_type='funds_auto_released'
        ).exists())
        self.assertIn(f"Successfully auto-released funds for order {order.order_id}.", out.getvalue())

    def test_auto_release_order_not_awaiting_release(self):
        """
        Ensure command skips orders not in 'awaiting_release' status.
        """
        order = self._create_order_with_escrow(self.client_user, self.technician_user, Decimal('100.00'), status='in_progress', auto_release_delta=timedelta(days=-1))
        
        initial_client_escrow = self.client_user.in_escrow_balance
        initial_technician_pending = self.technician_user.pending_balance

        out = StringIO()
        sys.stdout = out
        call_command('check_auto_release', stdout=out)
        sys.stdout = sys.__stdout__

        order.refresh_from_db()
        self.client_user.refresh_from_db()
        self.technician_user.refresh_from_db()

        self.assertEqual(order.order_status, 'in_progress') # Status should not change
        self.assertEqual(self.client_user.in_escrow_balance, initial_client_escrow)
        self.assertEqual(self.technician_user.pending_balance, initial_technician_pending)
        self.assertFalse(Transaction.objects.filter(transaction_type='escrow_release').exists())
        # The command filters out orders not in 'awaiting_release' status at the start,
        # so this message will not be in the output for such orders.
        self.assertIn("Auto-release check completed. Processed 0 orders.", out.getvalue())

    def test_auto_release_date_not_passed(self):
        """
        Ensure command skips orders where auto_release_date is in the future.
        """
        order = self._create_order_with_escrow(self.client_user, self.technician_user, Decimal('100.00'), status='awaiting_release', auto_release_delta=timedelta(days=1))
        
        initial_client_escrow = self.client_user.in_escrow_balance
        initial_technician_pending = self.technician_user.pending_balance

        out = StringIO()
        sys.stdout = out
        call_command('check_auto_release', stdout=out)
        sys.stdout = sys.__stdout__

        order.refresh_from_db()
        self.client_user.refresh_from_db()
        self.technician_user.refresh_from_db()

        self.assertEqual(order.order_status, 'awaiting_release') # Status should not change
        self.assertEqual(self.client_user.in_escrow_balance, initial_client_escrow)
        self.assertEqual(self.technician_user.pending_balance, initial_technician_pending)
        self.assertFalse(Transaction.objects.filter(transaction_type='escrow_release').exists())
        self.assertIn("Auto-release check completed. Processed 0 orders.", out.getvalue()) # No orders processed

    def test_auto_release_no_assigned_technician(self):
        """
        Ensure command handles orders with no assigned technician gracefully.
        """
        order = Order.objects.create(
            client_user=self.client_user,
            service=self.service,
            order_type='Installation', # Added required field
            problem_description='Order without technician', # Renamed 'description' to 'problem_description'
            requested_location='Another Location', # Added required field
            scheduled_date=timezone.now().date(), # Added required field
            scheduled_time_start='10:00', # Added required field
            scheduled_time_end='18:00', # Added required field
            order_status='awaiting_release',
            final_price=Decimal('100.00'),
            auto_release_date=timezone.now() - timedelta(days=1)
        )
        self.client_user.in_escrow_balance += Decimal('100.00')
        self.client_user.save()

        initial_client_escrow = self.client_user.in_escrow_balance

        out = StringIO()
        sys.stdout = out
        call_command('check_auto_release', stdout=out)
        sys.stdout = sys.__stdout__

        order.refresh_from_db()
        self.client_user.refresh_from_db()

        self.assertEqual(order.order_status, 'awaiting_release') # Status should not change
        self.assertEqual(self.client_user.in_escrow_balance, initial_client_escrow) # Escrow not touched
        self.assertIn(f"Order {order.order_id} has no assigned technician. Cannot auto-release funds.", out.getvalue())
        self.assertTrue(Notification.objects.filter(
            user=self.client_user,
            notification_type='auto_release_failed'
        ).exists())
        self.assertIn("Auto-release check completed. Processed 0 orders.", out.getvalue())

    def test_auto_release_insufficient_escrow_funds(self):
        """
        Ensure command handles cases where escrow funds are unexpectedly insufficient.
        """
        order = self._create_order_with_escrow(self.client_user, self.technician_user, Decimal('100.00'), status='awaiting_release', auto_release_delta=timedelta(days=-1))
        
        # Manually tamper with escrow to simulate insufficient funds
        self.client_user.in_escrow_balance -= Decimal('50.00') # Make it 50.00 instead of 100.00
        self.client_user.save()

        initial_client_escrow = self.client_user.in_escrow_balance
        initial_technician_pending = self.technician_user.pending_balance

        out = StringIO()
        sys.stdout = out
        call_command('check_auto_release', stdout=out)
        sys.stdout = sys.__stdout__

        order.refresh_from_db()
        self.client_user.refresh_from_db()
        self.technician_user.refresh_from_db()

        self.assertEqual(order.order_status, 'awaiting_release') # Status should not change
        self.assertEqual(self.client_user.in_escrow_balance, initial_client_escrow) # Escrow not touched
        self.assertEqual(self.technician_user.pending_balance, initial_technician_pending) # Pending not touched
        self.assertIn(f"Order {order.order_id}: Insufficient escrow funds ({initial_client_escrow}) to release {Decimal('100.00')}.", out.getvalue())
        self.assertTrue(Notification.objects.filter(
            user=self.client_user,
            notification_type='auto_release_failed'
        ).exists())
        self.assertIn("Auto-release check completed. Processed 0 orders.", out.getvalue())

    def test_auto_release_multiple_orders(self):
        """
        Ensure multiple orders are processed correctly in one run.
        """
        order1 = self._create_order_with_escrow(self.client_user, self.technician_user, Decimal('100.00'), status='awaiting_release', auto_release_delta=timedelta(days=-1))
        client_user_2 = User.objects.create_user(
            email='client2@example.com', password='password123', first_name='Client2', last_name='User', user_type_name='client', available_balance=Decimal('500.00'), in_escrow_balance=Decimal('0.00')
        )
        technician_user_2 = User.objects.create_user(
            email='tech2@example.com', password='password123', first_name='Tech2', last_name='User', user_type_name='technician', available_balance=Decimal('500.00'), pending_balance=Decimal('0.00')
        )
        # Create a verification document for the second technician
        VerificationDocument.objects.create(
            technician_user=technician_user_2,
            document_type='ID Card',
            document_url='http://example.com/id_tech2.jpg',
            upload_date=timezone.now().date(),
            verification_status='Approved'
        )
        order2 = self._create_order_with_escrow(client_user_2, technician_user_2, Decimal('75.00'), status='awaiting_release', auto_release_delta=timedelta(days=-2))

        initial_client1_escrow = self.client_user.in_escrow_balance
        initial_tech1_pending = self.technician_user.pending_balance
        initial_client2_escrow = client_user_2.in_escrow_balance
        initial_tech2_pending = technician_user_2.pending_balance

        out = StringIO()
        sys.stdout = out
        call_command('check_auto_release', stdout=out)
        sys.stdout = sys.__stdout__

        order1.refresh_from_db() # Refresh orders to get the latest status
        order2.refresh_from_db()
        self.client_user.refresh_from_db()
        self.technician_user.refresh_from_db()
        client_user_2.refresh_from_db()
        technician_user_2.refresh_from_db()

        self.assertEqual(order1.order_status, 'completed')
        self.assertEqual(order2.order_status, 'completed')

        self.assertEqual(self.client_user.in_escrow_balance, initial_client1_escrow - Decimal('100.00'))
        self.assertEqual(self.technician_user.pending_balance, initial_tech1_pending + Decimal('100.00'))
        self.assertEqual(client_user_2.in_escrow_balance, initial_client2_escrow - Decimal('75.00'))
        self.assertEqual(technician_user_2.pending_balance, initial_tech2_pending + Decimal('75.00'))

        self.assertTrue(Notification.objects.filter(user=self.technician_user, notification_type='funds_auto_released').exists())
        self.assertTrue(Notification.objects.filter(user=self.client_user, notification_type='funds_auto_released').exists())
        self.assertTrue(Notification.objects.filter(user=technician_user_2, notification_type='funds_auto_released').exists())
        self.assertTrue(Notification.objects.filter(user=client_user_2, notification_type='funds_auto_released').exists())

        self.assertIn(f"Successfully auto-released funds for order {order1.order_id}.", out.getvalue())
        self.assertIn(f"Successfully auto-released funds for order {order2.order_id}.", out.getvalue())
        self.assertIn("Auto-release check completed. Processed 2 orders.", out.getvalue())
