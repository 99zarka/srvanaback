from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from users.models import User, UserType
from orders.models import Order, ProjectOffer
from services.models import Service, ServiceCategory
from transactions.models import Transaction
from disputes.models import Dispute
from django.utils import timezone
from datetime import timedelta
from django.db import transaction as db_transaction
from technicians.models import VerificationDocument # Added for technician verification documents

class OrderViewsTest(APITestCase):
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
            available_balance=1000.00
        )
        self.technician_user = User.objects.create_user(
            email='tech@example.com',
            password='password123',
            first_name='Tech',
            last_name='User',
            user_type_name='technician', # Pass user_type_name string
            available_balance=500.00
        )
        # Create a verification document for the technician
        VerificationDocument.objects.create(
            technician_user=self.technician_user,
            document_type='ID Card',
            document_url='http://example.com/id_tech1.jpg',
            upload_date=timezone.now().date(),
            verification_status='Approved'
        )

        self.technician_user_2 = User.objects.create_user(
            email='tech2@example.com',
            password='password123',
            first_name='Tech2',
            last_name='User2',
            user_type_name='technician', # Pass user_type_name string
            available_balance=500.00
        )
        # Create a verification document for the second technician
        VerificationDocument.objects.create(
            technician_user=self.technician_user_2,
            document_type='ID Card',
            document_url='http://example.com/id_tech2.jpg',
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
        # Create a Service
        self.service = Service.objects.create(
            category=self.service_category,
            service_name='Plumbing',
            description='Professional plumbing services',
            service_type='hourly', # Or 'fixed_price', adjust as needed
            base_inspection_fee=25.00,
            estimated_price_range_min=80.00,
            estimated_price_range_max=150.00
        )

        # URLs
        self.order_list_url = '/api/orders/'
        self.offer_list_url = '/api/orders/projectoffers/'

    def test_create_order_by_client(self):
        """
        Ensure client can create an order.
        """
        data = {
            'service': self.service.service_id,
            'order_type': 'on_demand',
            'problem_description': 'Fix my leaky faucet',
            'requested_location': '123 Main St',
            'scheduled_date': (timezone.now() + timedelta(days=5)).date().isoformat(),
            'scheduled_time_start': '09:00',
            'scheduled_time_end': '17:00'
        }
        response = self.client_api.post(self.order_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.client_user, self.client_user)
        self.assertEqual(order.order_status, 'OPEN') # Default status should be OPEN
        # No transaction is created on order creation as per the updated perform_create
        self.assertFalse(Transaction.objects.filter(order=order, transaction_type='order_created').exists())
        # Verify notification for technician
        from notifications.models import Notification # Import Notification model for assertion
        self.assertTrue(Notification.objects.filter(user=self.technician_user, notification_type='new_project_available', related_order=order).exists())
    def test_accept_offer_sufficient_funds(self):
        """
        Ensure client can accept an offer with sufficient funds.
        """
        order = Order.objects.create(
            client_user=self.client_user,
            service=self.service,
            order_type='on_demand',
            problem_description='Install new sink',
            requested_location='Test Location',
            scheduled_date=(timezone.now() + timedelta(days=1)).date(),
            scheduled_time_start='09:00',
            scheduled_time_end='17:00',
            order_status='OPEN',
            final_price=0.00 # Should be updated
        )
        offer = ProjectOffer.objects.create(
            order=order,
            technician_user=self.technician_user,
            offered_price=150.00,
            status='pending',
            offer_date=timezone.now().date(),
            offer_initiator='technician'
        )

        # Create another offer which should be rejected when the first is accepted
        rejected_offer = ProjectOffer.objects.create(
            order=order,
            technician_user=self.technician_user_2,
            offered_price=100.00,
            status='pending',
            offer_date=timezone.now().date(),
            offer_initiator='technician'
        )
        
        url = f'/api/orders/{order.order_id}/accept-offer/{offer.offer_id}/'
        response = self.client_api.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.client_user.refresh_from_db()
        self.technician_user.refresh_from_db()

        self.assertEqual(order.order_status, 'ACCEPTED')
        self.assertEqual(order.technician_user, self.technician_user)
        self.assertEqual(order.final_price, 150.00)
        self.assertEqual(self.client_user.available_balance, 1000.00 - 150.00)
        self.assertEqual(self.client_user.in_escrow_balance, 150.00)
        self.assertTrue(order.job_start_timestamp is not None)
        self.assertTrue(order.auto_release_date is not None)

        # Verify transaction
        self.assertTrue(Transaction.objects.filter(
            source_user=self.client_user,
            destination_user=self.technician_user,
            order=order,
            transaction_type='ESCROW_HOLD',
            amount=150.00, 
        ).exists())
        # Verify notifications (implementation details may vary)
        self.assertTrue(self.technician_user.notifications.filter(notification_type='offer_accepted').exists())
        self.assertTrue(self.technician_user.notifications.filter(notification_type='offer_accepted').exists())
        self.assertTrue(self.client_user.notifications.filter(notification_type='offer_accepted').exists())

        # Verify other offers for this order are rejected
        rejected_offer.refresh_from_db() # Refresh after API call
        self.assertEqual(rejected_offer.status, 'rejected')
        self.assertTrue(self.technician_user_2.notifications.filter(notification_type='offer_rejected').exists())


    def test_accept_offer_insufficient_funds(self):
        """
        Ensure client cannot accept an offer with insufficient funds.
        """
        order = Order.objects.create(
            client_user=self.client_user,
            service=self.service,
            order_type='on_demand',
            problem_description='Install new sink',
            requested_location='Test Location',
            scheduled_date=(timezone.now() + timedelta(days=1)).date(),
            scheduled_time_start='09:00',
            scheduled_time_end='17:00',
            order_status='OPEN'
        )
        offer = ProjectOffer.objects.create(
            order=order,
            technician_user=self.technician_user,
            offered_price=1500.00, # More than client's available balance
            status='pending',
            offer_date=timezone.now().date(),
            offer_initiator='technician'
        )
        
        url = f'/api/orders/{order.order_id}/accept-offer/{offer.offer_id}/'
        response = self.client_api.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient available balance', response.data['detail'])

        order.refresh_from_db()
        self.client_user.refresh_from_db()
        self.assertEqual(order.order_status, 'OPEN')
        self.assertEqual(self.client_user.available_balance, 1000.00)
        self.assertEqual(self.client_user.in_escrow_balance, 0.00)
        self.assertFalse(Transaction.objects.filter(transaction_type='ESCROW_HOLD').exists()) # Updated transaction type

    def test_decline_offer(self):
        """
        Ensure client can decline an offer.
        """
        order = Order.objects.create(
            client_user=self.client_user,
            service=self.service,
            order_type='on_demand',
            problem_description='Fix my fence',
            requested_location='Test Location',
            scheduled_date=(timezone.now() + timedelta(days=1)).date(),
            scheduled_time_start='09:00',
            scheduled_time_end='17:00',
            order_status='OPEN'
        )
        offer = ProjectOffer.objects.create(
            order=order,
            technician_user=self.technician_user,
            offered_price=50.00,
            status='pending',
            offer_date=timezone.now().date(),
            offer_initiator='technician'
        )
        url = f'/api/orders/{order.order_id}/decline-offer/{offer.offer_id}/'
        response = self.client_api.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        offer.refresh_from_db()
        self.assertEqual(offer.status, 'rejected')
        self.assertTrue(self.technician_user.notifications.filter(notification_type='offer_declined').exists())

    def test_mark_job_done(self):
        """
        Ensure technician can mark a job as done.
        """
        order = Order.objects.create(
            client_user=self.client_user,
            technician_user=self.technician_user,
            service=self.service,
            order_type='on_demand',
            problem_description='Repair fridge',
            requested_location='Test Location',
            scheduled_date=(timezone.now() + timedelta(days=1)).date(),
            scheduled_time_start='09:00',
            scheduled_time_end='17:00',
            order_status='IN_PROGRESS',
            final_price=200.00
        )
        url = f'/api/orders/{order.order_id}/mark-job-done/'
        response = self.technician_api.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.order_status, 'AWAITING_RELEASE')
        self.assertTrue(order.job_done_timestamp is not None)
        self.assertTrue(self.client_user.notifications.filter(notification_type='job_done').exists())

    def test_mark_job_done_unauthorized(self):
        """
        Ensure unauthorized users cannot mark a job as done.
        """
        order = Order.objects.create(
            client_user=self.client_user,
            technician_user=self.technician_user,
            service=self.service,
            order_type='on_demand',
            problem_description='Repair fridge',
            requested_location='Test Location',
            scheduled_date=(timezone.now() + timedelta(days=1)).date(),
            scheduled_time_start='09:00',
            scheduled_time_end='17:00',
            order_status='IN_PROGRESS',
            final_price=200.00
        )
        url = f'/api/orders/{order.order_id}/mark-job-done/'
        # Client tries to mark job done
        response = self.client_api.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Another technician tries to mark job done
        self.technician_api.force_authenticate(user=self.technician_user_2)
        response = self.technician_api.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_release_funds(self):
        """
        Ensure client can release funds.
        """
        self.client_user.in_escrow_balance = 200.00
        self.client_user.save()

        order = Order.objects.create(
            client_user=self.client_user,
            technician_user=self.technician_user,
            service=self.service,
            order_type='on_demand',
            problem_description='Clean office',
            requested_location='Test Location',
            scheduled_date=(timezone.now() + timedelta(days=1)).date(),
            scheduled_time_start='09:00',
            scheduled_time_end='17:00',
            order_status='AWAITING_RELEASE',
            final_price=200.00
        )
        url = f'/api/orders/{order.order_id}/release-funds/'
        response = self.client_api.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.client_user.refresh_from_db()
        self.technician_user.refresh_from_db()

        self.assertEqual(order.order_status, 'COMPLETED')
        self.assertEqual(self.client_user.in_escrow_balance, 0.00)
        self.assertEqual(self.technician_user.pending_balance, 200.00)
        self.assertTrue(order.job_completion_timestamp is not None)

        self.assertTrue(Transaction.objects.filter(
            source_user=self.client_user, 
            destination_user=self.technician_user,
            order=order,
            transaction_type='ESCROW_RELEASE', 
            amount=200.00, 
        ).exists())
        self.assertTrue(self.technician_user.notifications.filter(notification_type='funds_released').exists())

    def test_release_funds_unauthorized(self):
        """
        Ensure unauthorized users cannot release funds.
        """
        self.client_user.in_escrow_balance = 200.00
        self.client_user.save()

        order = Order.objects.create(
            client_user=self.client_user,
            technician_user=self.technician_user,
            service=self.service,
            order_type='on_demand',
            problem_description='Clean office',
            requested_location='Test Location',
            scheduled_date=(timezone.now() + timedelta(days=1)).date(),
            scheduled_time_start='09:00',
            scheduled_time_end='17:00',
            order_status='awaiting_release',
            final_price=200.00
        )
        url = f'/api/orders/{order.order_id}/release-funds/'
        # Technician tries to release funds
        response = self.technician_api.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_initiate_dispute(self):
        """
        Ensure client can initiate a dispute.
        """
        order = Order.objects.create(
            client_user=self.client_user,
            technician_user=self.technician_user,
            service=self.service,
            order_type='on_demand',
            problem_description='Unsatisfactory work',
            requested_location='Test Location',
            scheduled_date=(timezone.now() + timedelta(days=1)).date(),
            scheduled_time_start='09:00',
            scheduled_time_end='17:00',
            order_status='AWAITING_RELEASE',
            final_price=100.00
        )
        data = {'client_argument': 'Technician left job incomplete.'}
        url = f'/api/orders/{order.order_id}/initiate-dispute/'
        response = self.client_api.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.order_status, 'DISPUTED')
        self.assertTrue(Dispute.objects.filter(order=order, initiator=self.client_user, status='OPEN', client_argument='Technician left job incomplete.').exists())
        self.assertTrue(self.technician_user.notifications.filter(notification_type='dispute_initiated').exists())
        self.assertTrue(self.admin_user.notifications.filter(notification_type='dispute_new').exists())
        # No transaction is created on dispute initiation
        self.assertFalse(Transaction.objects.filter(order=order, transaction_type='dispute_resolution').exists())

    def test_cancel_order_open(self):
        """
        Ensure client can cancel an open order without funds in escrow.
        """
        order = Order.objects.create(
            client_user=self.client_user,
            service=self.service,
            order_type='on_demand',
            problem_description='Decided not to proceed',
            requested_location='Test Location',
            scheduled_date=(timezone.now() + timedelta(days=1)).date(),
            scheduled_time_start='09:00',
            scheduled_time_end='17:00',
            order_status='OPEN',
            final_price=0.00
        )
        url = f'/api/orders/{order.order_id}/cancel-order/'
        response = self.client_api.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.client_user.refresh_from_db()
        self.assertEqual(order.order_status, 'CANCELLED')
        self.assertEqual(self.client_user.available_balance, 1000.00)
        self.assertEqual(self.client_user.in_escrow_balance, 0.00)
        self.assertFalse(Transaction.objects.filter(order=order, transaction_type='CANCEL_REFUND').exists()) # No refund transaction for open order
        self.assertTrue(self.client_user.notifications.filter(notification_type='order_cancelled').exists())

    def test_cancel_order_accepted_with_escrow(self):
        """
        Ensure client can cancel an accepted order and receive refund from escrow.
        """
        self.client_user.available_balance = 500.00 # Reduce available to test escrow logic
        self.client_user.in_escrow_balance = 200.00
        self.client_user.save()

        order = Order.objects.create(
            client_user=self.client_user,
            technician_user=self.technician_user,
            service=self.service,
            order_type='on_demand',
            problem_description='Changed my mind',
            requested_location='Test Location',
            scheduled_date=(timezone.now() + timedelta(days=1)).date(),
            scheduled_time_start='09:00',
            scheduled_time_end='17:00',
            order_status='ACCEPTED',
            final_price=200.00
        )
        url = f'/api/orders/{order.order_id}/cancel-order/'
        response = self.client_api.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.client_user.refresh_from_db()
        self.technician_user.refresh_from_db() # Technician should be notified

        self.assertEqual(order.order_status, 'REFUNDED')
        self.assertEqual(self.client_user.available_balance, 500.00 + 200.00) # Funds returned
        self.assertEqual(self.client_user.in_escrow_balance, 0.00)
        self.assertTrue(Transaction.objects.filter(
            source_user=self.client_user,
            destination_user=self.client_user,
            order=order,
            transaction_type='CANCEL_REFUND', 
            amount=200.00, 
        ).exists())
        self.assertTrue(self.client_user.notifications.filter(notification_type='order_cancelled').exists())
        self.assertTrue(self.technician_user.notifications.filter(notification_type='order_cancelled').exists())

    def test_cancel_order_by_admin(self):
        """
        Ensure admin can cancel an order.
        """
        self.client_user.available_balance = 500.00
        self.client_user.in_escrow_balance = 200.00
        self.client_user.save()

        order = Order.objects.create(
            client_user=self.client_user,
            technician_user=self.technician_user,
            service=self.service,
            order_type='on_demand',
            problem_description='Admin cancelled',
            requested_location='Test Location',
            scheduled_date=(timezone.now() + timedelta(days=1)).date(),
            scheduled_time_start='09:00',
            scheduled_time_end='17:00',
            order_status='IN_PROGRESS',
            final_price=200.00
        )
        url = f'/api/orders/{order.order_id}/cancel-order/'
        response = self.admin_api.post(url) # Admin cancels
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.client_user.refresh_from_db()
        self.technician_user.refresh_from_db()

        self.assertEqual(order.order_status, 'REFUNDED')
        self.assertEqual(self.client_user.available_balance, 500.00 + 200.00)
        self.assertEqual(self.client_user.in_escrow_balance, 0.00)
        self.assertTrue(Transaction.objects.filter(
            source_user=self.client_user,
            destination_user=self.client_user,
            order=order,
            transaction_type='CANCEL_REFUND',
            amount=200.00,
        ).exists())
        self.assertTrue(self.client_user.notifications.filter(notification_type='order_cancelled').exists())
        self.assertTrue(self.technician_user.notifications.filter(notification_type='order_cancelled').exists())

    def test_cancel_order_unauthorized(self):
        """
        Ensure an unauthorized user (another client/technician) cannot cancel an order.
        """
        client_user_other = User.objects.create_user(
            email='otherclient@example.com',
            password='password123',
            first_name='Other',
            last_name='Client',
            user_type=self.client_user_type,
            available_balance=100.00
        )
        client_api_other = APIClient()
        client_api_other.force_authenticate(user=client_user_other)

        order = Order.objects.create(
            client_user=self.client_user,
            service=self.service,
            order_type='on_demand',
            problem_description='Unauthorized cancel attempt',
            requested_location='Test Location',
            scheduled_date=(timezone.now() + timedelta(days=1)).date(),
            scheduled_time_start='09:00',
            scheduled_time_end='17:00',
            order_status='OPEN',
            final_price=0.00
        )
        url = f'/api/orders/{order.order_id}/cancel-order/'
        response = client_api_other.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'OPEN') # Still OPEN
