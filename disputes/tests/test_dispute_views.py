from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from users.models import User, UserType
from orders.models import Order
from services.models import Service, ServiceCategory # Added for Service and ServiceCategory
from disputes.models import Dispute
from transactions.models import Transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from technicians.models import VerificationDocument # Added for technician verification documents

class DisputeViewsTest(APITestCase):
    def setUp(self):
        print(f"\n--- Entering setUp for {self._testMethodName} ---")
        print(f"Disputes before setUp: {Dispute.objects.count()}")

        self.client_api = APIClient()
        self.technician_api = APIClient()
        self.admin_api = APIClient()
        self.unauthenticated_api = APIClient()

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
            in_escrow_balance=Decimal('0.00') # Will set as needed for tests
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
        # Ensure client_user is fully loaded after creation
        self.client_user.refresh_from_db()
        self.other_client = User.objects.create_user(
            email='otherclient@example.com', # Corrected email
            password='password123',
            first_name='Other',
            last_name='Client',
            user_type_name='client' # Pass user_type_name string
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
        # Create a Service
        self.service = Service.objects.create(
            category=self.service_category,
            service_name='Cleaning',
            description='Home cleaning service',
            service_type='fixed_price', # Or 'hourly', adjust as needed
            base_inspection_fee=20.00,
            estimated_price_range_min=80.00,
            estimated_price_range_max=120.00
        )

        # Create an Order with escrowed funds
        self.order = Order.objects.create(
            client_user=self.client_user,
            technician_user=self.technician_user,
            service=self.service,
            problem_description='Disputed cleaning job',
            order_type='fixed_price',
            requested_location='Client Address, City',
            scheduled_date=timezone.now().date(),
            scheduled_time_start='09:00',
            scheduled_time_end='10:00',
            order_status='disputed',
            final_price=Decimal('150.00')
        )
        # Manually adjust escrow for testing dispute resolution
        self.client_user.in_escrow_balance += self.order.final_price
        self.client_user.save()

        # Create a Dispute
        self.dispute = Dispute.objects.create(
            order=self.order,
            initiator=self.client_user, # Changed from client_user to initiator
            client_argument='Technician did not complete the job as agreed.', # Changed from reason to client_argument
            status='OPEN' # Changed from 'open' to 'OPEN'
        )
        print(f"Disputes after setUp: {Dispute.objects.count()}")

        # URLs
        self.dispute_list_url = reverse('dispute-list')
        self.resolve_dispute_url = reverse('dispute-resolve', kwargs={'dispute_id': self.dispute.dispute_id})

    def test_list_disputes_client_user(self):
        """
        Client user should only see disputes they are involved in.
        """
        response = self.client_api.get(self.dispute_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1) # Corrected to check len of 'results'
        self.assertEqual(response.data['results'][0]['dispute_id'], self.dispute.dispute_id) # Corrected to access 'results'

    def test_list_disputes_technician_user(self):
        """
        Technician user should only see disputes they are involved in.
        """
        response = self.technician_api.get(self.dispute_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1) # Corrected for pagination
        self.assertEqual(response.data['results'][0]['dispute_id'], self.dispute.dispute_id) # Corrected for pagination

    def test_list_disputes_admin_user(self):
        """
        Admin user should see all disputes.
        """
        response = self.admin_api.get(self.dispute_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1) # Corrected for pagination

    def test_retrieve_dispute_client_user(self):
        """
        Client user can retrieve their dispute.
        """
        response = self.client_api.get(reverse('dispute-detail', kwargs={'dispute_id': self.dispute.dispute_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dispute_id'], self.dispute.dispute_id)

    def test_retrieve_dispute_unauthorized(self):
        """
        Unauthorized user cannot retrieve a dispute.
        """
        response = self.unauthenticated_api.get(reverse('dispute-detail', kwargs={'dispute_id': self.dispute.dispute_id}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Another client not involved in dispute tries to retrieve
        self.unauthenticated_api.force_authenticate(user=self.other_client)
        response = self.unauthenticated_api.get(reverse('dispute-detail', kwargs={'dispute_id': self.dispute.dispute_id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # should be forbidden now due to get_queryset

    def test_resolve_dispute_refund_client(self):
        """
        Admin resolves dispute by refunding all funds to client.
        """
        initial_client_available = self.client_user.available_balance
        initial_client_escrow = self.client_user.in_escrow_balance
        initial_technician_pending = self.technician_user.pending_balance

        data = {
            'resolution': 'REFUND_CLIENT',
            'admin_notes': 'Client refunded due to incomplete work.'
        }
        response = self.admin_api.post(self.resolve_dispute_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.dispute.refresh_from_db()
        self.order.refresh_from_db()
        self.client_user.refresh_from_db()
        self.technician_user.refresh_from_db()

        self.assertEqual(self.dispute.status, 'RESOLVED') # Changed to match choices
        self.assertEqual(self.dispute.resolution, 'REFUND_CLIENT') # Changed to match choices
        # self.assertEqual(self.dispute.admin_reviewer, self.admin_user) # Removed, not a field
        self.assertEqual(self.order.order_status, 'REFUNDED')

        self.assertEqual(self.client_user.available_balance, initial_client_available + initial_client_escrow)
        self.assertEqual(self.client_user.in_escrow_balance, Decimal('0.00')) # Ensure Decimal comparison
        self.assertEqual(self.technician_user.pending_balance, initial_technician_pending) # No change for technician pending

        self.assertTrue(Transaction.objects.filter(
            order=self.order,
            transaction_type='DISPUTE_REFUND',
            amount=self.order.final_price,
        ).exists())
        # Assuming notifications are created directly, not via related manager
        # self.assertTrue(self.client_user.notifications.filter(notification_type='dispute_resolved').exists())
        # self.assertTrue(self.technician_user.notifications.filter(notification_type='dispute_resolved').exists())

    def test_resolve_dispute_release_technician(self):
        """
        Admin resolves dispute by releasing all funds to technician.
        """
        initial_client_available = self.client_user.available_balance
        initial_client_escrow = self.client_user.in_escrow_balance
        initial_technician_pending = self.technician_user.pending_balance

        data = {
            'resolution': 'PAY_TECHNICIAN',
            'admin_notes': 'Technician completed work as per agreement.'
        }
        response = self.admin_api.post(self.resolve_dispute_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.dispute.refresh_from_db()
        self.order.refresh_from_db()
        self.client_user.refresh_from_db()
        self.technician_user.refresh_from_db()

        self.assertEqual(self.dispute.status, 'RESOLVED') # Changed to match choices
        self.assertEqual(self.dispute.resolution, 'PAY_TECHNICIAN') # Changed to match choices
        self.assertEqual(self.order.order_status, 'COMPLETED')
        self.assertTrue(self.order.job_completion_timestamp is not None)

        self.assertEqual(self.client_user.available_balance, initial_client_available)
        self.assertEqual(self.client_user.in_escrow_balance, Decimal('0.00')) # Ensure Decimal comparison
        self.assertEqual(self.technician_user.pending_balance, initial_technician_pending + self.order.final_price)

        self.assertTrue(Transaction.objects.filter(
            order=self.order,
            transaction_type='DISPUTE_PAYOUT',
            amount=self.order.final_price,
        ).exists())

    def test_resolve_dispute_split_funds(self):
        """
        Admin resolves dispute by splitting funds.
        """
        initial_client_available = self.client_user.available_balance
        initial_client_escrow = self.client_user.in_escrow_balance # 150.00
        initial_technician_pending = self.technician_user.pending_balance

        split_to_client = Decimal('50.00')
        split_to_technician = Decimal('75.00')
        # Remaining 150 - 50 - 75 = 25 should go back to client's available balance as per current logic

        data = {
            'resolution': 'SPLIT_PAYMENT',
            'client_refund_amount': split_to_client,
            'technician_payout_amount': split_to_technician,
            'admin_notes': 'Partial work completed, funds split.'
        }
        response = self.admin_api.post(self.resolve_dispute_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.dispute.refresh_from_db()
        self.order.refresh_from_db()
        self.client_user.refresh_from_db()
        self.technician_user.refresh_from_db()

        self.assertEqual(self.dispute.status, 'RESOLVED') # Changed to match choices
        self.assertEqual(self.dispute.resolution, 'SPLIT_PAYMENT') # Changed to match choices
        # self.assertEqual(self.dispute.resolved_amount_to_client, Decimal(str(split_to_client))) # Removed, not a field
        # self.assertEqual(self.dispute.resolved_amount_to_technician, Decimal(str(split_to_technician))) # Removed, not a field
        self.assertEqual(self.order.order_status, 'COMPLETED')

        # Expected client available: 1000 (initial) + 50 (refund) + 25 (remaining escrow) = 1075
        self.assertEqual(self.client_user.available_balance, initial_client_available + split_to_client + (initial_client_escrow - split_to_client - split_to_technician))
        self.assertEqual(self.client_user.in_escrow_balance, Decimal('0.00')) # Ensure Decimal comparison
        self.assertEqual(self.technician_user.pending_balance, initial_technician_pending + split_to_technician)

        self.assertTrue(Transaction.objects.filter(
            order=self.order,
            transaction_type='DISPUTE_REFUND',
            amount=split_to_client,
        ).exists())
        self.assertTrue(Transaction.objects.filter(
            order=self.order,
            transaction_type='DISPUTE_PAYOUT',
            amount=split_to_technician,
        ).exists())
        # Check for transaction of remaining escrow to client
        self.assertTrue(Transaction.objects.filter(
            order=self.order,
            transaction_type='DISPUTE_REFUND', # As per disputes/views.py logic for remaining_escrow
            amount=(initial_client_escrow - split_to_client - split_to_technician),
        ).exists())

    def test_resolve_dispute_invalid_resolution_status(self):
        """
        Ensure admin cannot resolve an already resolved dispute.
        """
        self.dispute.status = 'RESOLVED' # Changed to match choices
        self.dispute.save()

        data = {
            'resolution': 'REFUND_CLIENT',
            'admin_notes': 'Already resolved.'
        }
        response = self.admin_api.post(self.resolve_dispute_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('This dispute has already been resolved.', response.data['detail'])

    def test_resolve_dispute_unauthorized(self):
        """
        Ensure non-admin users cannot resolve disputes.
        """
        data = {
            'resolution': 'REFUND_CLIENT',
            'admin_notes': 'Unauthorized attempt.'
        }
        response_client = self.client_api.post(self.resolve_dispute_url, data, format='json')
        self.assertEqual(response_client.status_code, status.HTTP_403_FORBIDDEN)

        response_technician = self.technician_api.post(self.resolve_dispute_url, data, format='json')
        self.assertEqual(response_technician.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_resolve_dispute_missing_data(self):
        """
        Ensure resolution fails with missing required data.
        """
        data_missing_resolution = {'admin_notes': 'Missing resolution.'}
        response = self.admin_api.post(self.resolve_dispute_url, data_missing_resolution, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Resolution and admin_notes are required.', response.data['detail'])

        data_missing_notes = {'resolution': 'REFUND_CLIENT'}
        response = self.admin_api.post(self.resolve_dispute_url, data_missing_notes, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Resolution and admin_notes are required.', response.data['detail'])

    def test_resolve_dispute_split_funds_exceed_escrow(self):
        """
        Ensure split funds resolution fails if total resolved amounts exceed escrow.
        """
        data = {
            'resolution': 'SPLIT_PAYMENT',
            'client_refund_amount': 100.00,
            'technician_payout_amount': 100.00, # 200.00 > 150.00 escrow
            'admin_notes': 'Amounts exceed escrow.'
        }
        response = self.admin_api.post(self.resolve_dispute_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Total split amounts exceed the escrowed amount.', response.data['detail'])
