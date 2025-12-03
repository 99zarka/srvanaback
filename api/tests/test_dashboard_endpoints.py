from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from users.models import User, UserType
from orders.models import Order
from services.models import ServiceCategory, Service
from payments.models import Payment, PaymentMethod
from reviews.models import Review
from issue_reports.models import IssueReport
from datetime import date, datetime, timedelta
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

class DashboardEndpointsTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Create UserTypes
        self.client_usertype = UserType.objects.create(user_type_name="client")
        self.technician_usertype = UserType.objects.create(user_type_name="technician")
        self.admin_usertype = UserType.objects.create(user_type_name="admin")

        # Create Users
        self.admin_user = User.objects.create_superuser(
            username='adminuser', email='admin@example.com', password='adminpassword123',
            user_type_name=self.admin_usertype.user_type_name
        )
        self.technician_user = User.objects.create_user(
            username='techuser', email='technician@example.com', password='password123',
            user_type_name=self.technician_usertype.user_type_name
        )
        self.client_user = User.objects.create_user(
            username='clientuser', email='client@example.com', password='password123',
            user_type_name=self.client_usertype.user_type_name
        )
        self.other_technician_user = User.objects.create_user(
            username='othertech', email='othertech@example.com', password='password123',
            user_type_name=self.technician_usertype.user_type_name
        )
        self.other_client_user = User.objects.create_user(
            username='otherclient', email='otherclient@example.com', password='password123',
            user_type_name=self.client_usertype.user_type_name
        )

        # Technician users are already created with user_type_name="technician"
        # No need for separate Technician profiles if using User model directly


        # Create Service Categories and Services
        self.category = ServiceCategory.objects.create(category_name="Home Repair")
        self.service_1 = Service.objects.create(
            category=self.category,
            service_name="Pipe Fix",
            description="Fixing leaky pipes",
            base_inspection_fee=50.00,
            service_type="repair"
        )
        self.service_2 = Service.objects.create(
            category=self.category,
            service_name="Electrical Check",
            description="Checking home electrical systems",
            base_inspection_fee=75.00,
            service_type="inspection"
        )

        # Create Orders (for client-summary, worker-tasks)
        # Completed order for technician_user (from previous month)
        self.completed_order = Order.objects.create(
            client_user=self.client_user,
            service=self.service_1,
            technician_user=self.technician_user,
            order_type='repair',
            problem_description='Leaky pipe repair',
            requested_location='Client Address 1',
            scheduled_date=timezone.now().date() - timedelta(days=45),  # From previous month
            scheduled_time_start='09:00',
            scheduled_time_end='10:00',
            order_status='completed',
            final_price=200.00,
            creation_timestamp=timezone.now().date() - timedelta(days=47),
            job_completion_timestamp=timezone.now().date() - timedelta(days=45),  # From previous month
        )
        # Active order for technician_user
        self.active_order = Order.objects.create(
            client_user=self.client_user,
            service=self.service_2,
            technician_user=self.technician_user,
            order_type='inspection',
            problem_description='Electrical system check',
            requested_location='Client Address 1',
            scheduled_date=timezone.now().date() + timedelta(days=5),
            scheduled_time_start='11:00',
            scheduled_time_end='12:00',
            order_status='in_progress',
            final_price=150.00,
            creation_timestamp=timezone.now().date() - timedelta(days=2),
        )
        # Pending order for client_user
        self.pending_client_order = Order.objects.create(
            client_user=self.client_user,
            service=self.service_1,
            order_type='repair',
            problem_description='Water heater replacement',
            requested_location='Client Address 2',
            scheduled_date=timezone.now().date() + timedelta(days=2),
            scheduled_time_start='13:00',
            scheduled_time_end='14:00',
            order_status='pending',
            final_price=100.00,
            creation_timestamp=timezone.now().date() - timedelta(days=1),
        )
        # Another completed order for client_user
        self.another_completed_client_order = Order.objects.create(
            client_user=self.client_user,
            service=self.service_2,
            technician_user=self.other_technician_user,
            order_type='inspection',
            problem_description='HVAC system check',
            requested_location='Client Address 2',
            scheduled_date=timezone.now().date() - timedelta(days=20),
            scheduled_time_start='10:00',
            scheduled_time_end='11:00',
            order_status='completed',
            final_price=300.00,
            creation_timestamp=timezone.now().date() - timedelta(days=22),
            job_completion_timestamp=timezone.now().date() - timedelta(days=20),
        )

        # Create PaymentMethods
        self.credit_card_method = PaymentMethod.objects.create(
            user=self.client_user,
            card_type='Visa',
            last_four_digits='1111',
            expiration_date='12/2025',
            card_holder_name='Client User',
            is_default=True
        )
        self.paypal_method = PaymentMethod.objects.create(
            user=self.client_user,
            card_type='PayPal',
            last_four_digits='2222',
            expiration_date='11/2024',
            card_holder_name='Client User',
            is_default=False
        )

        # Create Payments
        self.payment_1 = Payment.objects.create(
            order=self.completed_order,
            user=self.client_user,
            amount=200.00,
            payment_method=self.credit_card_method,
            transaction_id='txn_12345',
            status='COMPLETED',
        )
        self.payment_2 = Payment.objects.create(
            order=self.another_completed_client_order,
            user=self.client_user,
            amount=300.00,
            payment_method=self.paypal_method,
            transaction_id='txn_67890',
            status='COMPLETED',
        )

        # Create Reviews - from previous month to avoid current month calculations
        # Use a fixed date that is definitely in the previous month and timezone-aware
        
        # Create a date from 2024 (definitely not current year) with timezone awareness
        previous_month_date = timezone.make_aware(
            datetime(2024, 1, 15, 12, 0, 0)
        )
        self.review_1 = Review.objects.create(
            order=self.completed_order,
            reviewer=self.client_user,
            technician=self.technician_user,
            rating=5,
            comment="Great service!",
            created_at=previous_month_date
        )
        self.review_2 = Review.objects.create(
            order=self.another_completed_client_order,
            reviewer=self.client_user,
            technician=self.other_technician_user,
            rating=4,
            comment="Good work.",
            created_at=previous_month_date
        )

        # Create Issue Reports
        self.issue_report_1 = IssueReport.objects.create(
            reporter=self.client_user,
            title="Damaged property",
            description="Technician caused damage.",
            status="open"
        )
        self.issue_report_2 = IssueReport.objects.create(
            reporter=self.other_client_user,
            title="Late arrival",
            description="Technician was late.",
            status="in_progress"
        )

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    # --- Technician Dashboard Endpoints ---
    def test_technician_earnings_summary_authenticated_technician(self):
        client = self.get_auth_client(self.technician_user)
        url = reverse('technician_earnings_summary') # Use the correct URL name
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_earnings', response.data)
        self.assertIn('this_month_earnings', response.data)
        self.assertIn('pending_earnings', response.data)
        # Add assertions for expected values based on setup data
        # For technician_user, total earnings should be from completed_order (200.00)
        self.assertEqual(float(response.data['total_earnings']), 200.00)
        # Assuming this month is current month, and completed_order is not in this month
        self.assertEqual(float(response.data['this_month_earnings']), 0.00)
        # No pending earnings were explicitly created for technician_user in setup
        self.assertEqual(float(response.data['pending_earnings']), 0.00)


    def test_technician_earnings_summary_authenticated_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        url = reverse('technician_earnings_summary')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_technician_earnings_summary_unauthenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('technician_earnings_summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_technician_worker_summary_authenticated_technician(self):
        client = self.get_auth_client(self.technician_user)
        url = reverse('technician_worker_summary')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('active_tasks', response.data)
        self.assertIn('completed_tasks', response.data)
        self.assertIn('total_earnings', response.data)
        self.assertIn('average_rating', response.data)
        # Based on setup: active_tasks = 1, completed_tasks = 1, total_earnings = 200, average_rating = 5.0
        self.assertEqual(response.data['active_tasks'], 1)
        self.assertEqual(response.data['completed_tasks'], 1)
        self.assertEqual(float(response.data['total_earnings']), 200.00)
        self.assertEqual(float(response.data['average_rating']), 5.0)

    def test_technician_worker_summary_authenticated_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        url = reverse('technician_worker_summary')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_technician_worker_summary_unauthenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('technician_worker_summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_technician_monthly_performance_authenticated_technician(self):
        client = self.get_auth_client(self.technician_user)
        url = reverse('technician_monthly_performance')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('completed_tasks_month', response.data)
        self.assertIn('earnings_month', response.data)
        self.assertIn('average_rating_month', response.data)
        # Based on setup, these should likely be 0 for current month unless orders were set for current month
        self.assertEqual(response.data['completed_tasks_month'], 0)
        self.assertEqual(float(response.data['earnings_month']), 0.00)
        # Review created in setUp is created "now", so it counts for this month
        self.assertEqual(float(response.data['average_rating_month']), 5.0)

    def test_technician_monthly_performance_authenticated_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        url = reverse('technician_monthly_performance')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_technician_monthly_performance_unauthenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('technician_monthly_performance')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_worker_reviews_authenticated_technician(self):
        client = self.get_auth_client(self.technician_user)
        url = reverse('reviews-worker-reviews') # Use the correct URL name
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('average_rating', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['average_rating'], 5.0)
        self.assertEqual(response.data['results'][0]['comment'], "Great service!")

    def test_worker_reviews_authenticated_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        url = reverse('reviews-worker-reviews')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_worker_reviews_unauthenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('reviews-worker-reviews')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Client Dashboard Endpoints ---
    def test_client_summary_authenticated_client(self):
        client = self.get_auth_client(self.client_user)
        url = reverse('client_summary')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('active_orders', response.data)
        self.assertIn('completed_orders', response.data)
        self.assertIn('total_spent', response.data)
        # Based on setup: active_orders = 2 (pending + in_progress), completed_orders = 2, total_spent = 500
        self.assertEqual(response.data['active_orders'], 2) # pending_client_order + active_order
        self.assertEqual(response.data['completed_orders'], 2) # completed_order, another_completed_client_order
        self.assertEqual(float(response.data['total_spent']), 500.00)

    def test_client_summary_authenticated_technician_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        url = reverse('client_summary')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_summary_unauthenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('client_summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_orders_list_authenticated_client(self):
        client = self.get_auth_client(self.client_user)
        url = reverse('orders:order-list') # Assuming a generic order list endpoint for clients
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 4) # Client_user has 4 orders

    def test_client_orders_list_authenticated_technician_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        url = reverse('orders:order-list')
        response = client.get(url)
        # Technician should not see all orders, but only their own related orders or none.
        # This assumes the 'order-list' endpoint has appropriate permissions.
        # If it's a generic list, a 403 or empty list might be expected depending on implementation.
        # For now, let's assume it should be forbidden or return an empty list if not tied to technician.
        # Given the previous context, generic orders list should be forbidden for a technician.
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_client_orders_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('orders:order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_payments_list_authenticated_client(self):
        client = self.get_auth_client(self.client_user)
        url = reverse('payment-list')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        # Check that both payments are present, order might be different
        amounts = [float(payment['amount']) for payment in response.data['results']]
        self.assertIn(200.00, amounts)
        self.assertIn(300.00, amounts)

    def test_client_payments_list_authenticated_technician_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        url = reverse('payment-list')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_payments_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('payment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Admin Dashboard Endpoints ---
    def test_admin_summary_authenticated_admin(self):
        client = self.get_auth_client(self.admin_user)
        url = reverse('admin_summary')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_users', response.data)
        self.assertIn('active_workers', response.data)
        self.assertIn('services_completed', response.data)
        self.assertIn('total_revenue', response.data)
        # Check counts
        self.assertEqual(response.data['total_users'], User.objects.count()) # Includes admin, 2 technicians, 2 clients
        self.assertEqual(response.data['active_workers'], 2) # Both technicians
        self.assertEqual(response.data['services_completed'], 2) # 2 completed orders
        self.assertEqual(float(response.data['total_revenue']), 500.00) # Sum of completed order prices

    def test_admin_summary_authenticated_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        url = reverse('admin_summary')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_summary_unauthenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('admin_summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_issue_reports_list_authenticated_admin(self):
        client = self.get_auth_client(self.admin_user)
        url = reverse('issuereport-list')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['title'], "Damaged property")

    def test_admin_issue_reports_list_authenticated_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        url = reverse('issuereport-list')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_issue_reports_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('issuereport-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_services_list_admin(self):
        client = self.get_auth_client(self.admin_user)
        url = reverse('service-list')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_services_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('service-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Services list should be public

    def test_public_users_paginated_admin(self):
        client = self.get_auth_client(self.admin_user)
        url = '/api/users/public/all/' + '?page=1&page_size=10'
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], User.objects.count()) # All users including admin

    def test_public_users_paginated_client(self):
        client = self.get_auth_client(self.client_user)
        url = '/api/users/public/all/' + '?page=1&page_size=10'
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], User.objects.count())

    def test_public_users_paginated_unauthenticated(self):
        self.client.force_authenticate(user=None)
        url = '/api/users/public/all/' + '?page=1&page_size=10'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], User.objects.count())
