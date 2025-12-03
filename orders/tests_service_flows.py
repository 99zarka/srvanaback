"""
Comprehensive test suite for service ordering flows backend endpoints.

This test file covers all the new functionality added for:
1. Client Posts Project, Technicians Apply, Client Hires flow
2. Client Hires Directly flow

Test coverage includes:
- OrderViewSet custom actions (available_for_offer, offers, accept_offer)
- UserViewSet technician browsing actions (technicians, technician_detail)
- Notification system integration
- Permission and authentication checks
- Edge cases and error handling
"""

from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import AnonymousUser
from unittest.mock import patch, MagicMock

from orders.models import Order, ProjectOffer
from services.models import ServiceCategory, Service
from users.models import UserType
from notifications.models import Notification

User = get_user_model()


class BaseTestCase(APITestCase):
    """Base test case with common setup for all tests."""
    
    def setUp(self):
        """Set up test data."""
        # Create user types
        self.client_user_type = UserType.objects.create(user_type_name='client')
        self.technician_user_type = UserType.objects.create(user_type_name='technician')
        self.admin_user_type = UserType.objects.create(user_type_name='admin')
        
        # Create test users
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='adminpass',
            first_name='Admin',
            last_name='User',
            user_type_name='admin',
            is_staff=True,
            is_superuser=True
        )
        
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='clientpass',
            first_name='Client',
            last_name='User',
            user_type_name='client'
        )
        
        self.technician_user1 = User.objects.create_user(
            email='tech1@test.com',
            password='techpass',
            first_name='Tech',
            last_name='One',
            user_type_name='technician',
            verification_status='verified',
            account_status='active',
            specialization='Plumbing',
            overall_rating=4.5,
            num_jobs_completed=10
        )
        
        self.technician_user2 = User.objects.create_user(
            email='tech2@test.com',
            password='techpass',
            first_name='Tech',
            last_name='Two',
            user_type_name='technician',
            verification_status='verified',
            account_status='active',
            specialization='Electrical',
            overall_rating=4.2,
            num_jobs_completed=15
        )
        
        self.technician_user3 = User.objects.create_user(
            email='tech3@test.com',
            password='techpass',
            first_name='Tech',
            last_name='Three',
            user_type_name='technician',
            verification_status='pending',  # Not verified
            account_status='active'
        )
        
        # Create services
        self.service_category = ServiceCategory.objects.create(category_name='Home Services')
        self.plumbing_service = Service.objects.create(
            category=self.service_category,
            service_name='Plumbing',
            description='Plumbing services',
            service_type='General',
            base_inspection_fee=50.00
        )
        self.electrical_service = Service.objects.create(
            category=self.service_category,
            service_name='Electrical',
            description='Electrical services',
            service_type='General',
            base_inspection_fee=60.00
        )
        
        # Create test orders
        self.available_order = Order.objects.create(
            service=self.plumbing_service,
            client_user=self.client_user,
            order_type='service_request',
            problem_description='Fix leaky faucet',
            requested_location='123 Main St, Cairo',
            scheduled_date=date(2025, 12, 1),
            scheduled_time_start='10:00',
            scheduled_time_end='12:00',
            creation_timestamp=date(2025, 11, 27),
            order_status='pending'
        )
        
        self.assigned_order = Order.objects.create(
            service=self.electrical_service,
            client_user=self.client_user,
            order_type='service_request',
            problem_description='Install light fixture',
            requested_location='456 Oak Ave, Alexandria',
            scheduled_date=date(2025, 12, 2),
            scheduled_time_start='14:00',
            scheduled_time_end='16:00',
            creation_timestamp=date(2025, 11, 27),
            order_status='accepted',
            technician_user=self.technician_user1
        )
        
        # Create test offers
        self.offer1 = ProjectOffer.objects.create(
            order=self.available_order,
            technician_user=self.technician_user1,
            offered_price=150.00,
            offer_description='Professional plumbing service',
            offer_date=date(2025, 11, 27),
            status='pending'
        )
        
        self.offer2 = ProjectOffer.objects.create(
            order=self.available_order,
            technician_user=self.technician_user2,
            offered_price=175.00,
            offer_description='Quality electrical work',
            offer_date=date(2025, 11, 27),
            status='pending'
        )
        
        # Set up API clients
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin_user)
        
        self.client_api = APIClient()
        self.client_api.force_authenticate(user=self.client_user)
        
        self.tech1_client = APIClient()
        self.tech1_client.force_authenticate(user=self.technician_user1)
        
        self.tech2_client = APIClient()
        self.tech2_client.force_authenticate(user=self.technician_user2)
        
        self.tech3_client = APIClient()
        self.tech3_client.force_authenticate(user=self.technician_user3)
        
        self.anonymous_client = APIClient()


class OrderAvailableForOfferTests(BaseTestCase):
    """Test OrderViewSet.available_for_offer endpoint."""
    
    def test_technician_can_view_available_orders(self):
        """Test that verified technicians can view available orders."""
        url = reverse('orders:order-available-for-offer')
        response = self.tech1_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return the available order
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['order_id'], self.available_order.order_id)
    
    def test_unverified_technician_cannot_view_available_orders(self):
        """Test that unverified technicians cannot view available orders."""
        url = reverse('orders:order-available-for-offer')
        response = self.tech3_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_client_cannot_view_available_orders(self):
        """Test that clients cannot access available orders endpoint."""
        url = reverse('orders:order-available-for-offer')
        response = self.client_api.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_anonymous_user_cannot_view_available_orders(self):
        """Test that anonymous users cannot view available orders."""
        url = reverse('orders:order-available-for-offer')
        response = self.anonymous_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_available_orders_filtered_correctly(self):
        """Test that only orders without assigned technicians are returned."""
        # Create another order with assigned technician
        Order.objects.create(
            service=self.plumbing_service,
            client_user=self.client_user,
            order_type='service_request',
            problem_description='Another order',
            requested_location='789 Elm St, Giza',
            scheduled_date=date(2025, 12, 3),
            scheduled_time_start='10:00',
            scheduled_time_end='12:00',
            creation_timestamp=date(2025, 11, 27),
            order_status='pending',
            technician_user=self.technician_user2
        )
        
        url = reverse('orders:order-available-for-offer')
        response = self.tech1_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['order_id'], self.available_order.order_id)


class OrderOffersTests(BaseTestCase):
    """Test OrderViewSet.offers endpoint."""
    
    def test_client_can_view_offers_for_their_order(self):
        """Test that clients can view offers for their orders."""
        url = reverse('orders:order-offers', kwargs={'pk': self.available_order.pk})
        response = self.client_api.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Check that offers are properly ordered by creation date
        offers = response.data['results']
        self.assertEqual(offers[0]['offer_id'], self.offer2.offer_id)
        self.assertEqual(offers[1]['offer_id'], self.offer1.offer_id)
    
    def test_admin_can_view_offers_for_any_order(self):
        """Test that admins can view offers for any order."""
        url = reverse('orders:order-offers', kwargs={'pk': self.available_order.pk})
        response = self.admin_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_technician_cannot_view_offers_for_others_orders(self):
        """Test that technicians cannot view offers for orders they don't own."""
        url = reverse('orders:order-offers', kwargs={'pk': self.available_order.order_id})
        response = self.tech1_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_client_cannot_view_offers_for_others_orders(self):
        """Test that clients cannot view offers for orders they don't own."""
        # Create another client
        another_client_user = User.objects.create_user(
            email='client2@test.com',
            password='clientpass',
            first_name='Client',
            last_name='Two',
            user_type_name='client'
        )
        
        another_client_api = APIClient()
        another_client_api.force_authenticate(user=another_client_user)
        
        url = reverse('orders:order-offers', kwargs={'pk': self.available_order.pk})
        response = another_client_api.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_returns_404_for_nonexistent_order(self):
        """Test that 404 is returned for non-existent orders."""
        url = reverse('orders:order-offers', kwargs={'pk': 99999})
        response = self.client_api.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderAcceptOfferTests(BaseTestCase):
    """Test OrderViewSet.accept_offer endpoint."""
    
    @patch('orders.views.Notification.objects.create')
    def test_client_can_accept_offer(self, mock_notification):
        """Test that clients can accept offers for their orders."""
        url = reverse('orders:order-accept-offer', kwargs={
            'pk': self.available_order.pk,
            'offer_id': self.offer1.offer_id
        })
        response = self.client_api.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Offer accepted successfully.')
        
        # Refresh from database
        self.available_order.refresh_from_db()
        self.offer1.refresh_from_db()
        
        # Check that order was assigned to technician
        self.assertEqual(self.available_order.technician_user, self.technician_user1)
        self.assertEqual(self.available_order.order_status, 'accepted')
        
        # Check that offer status was updated
        self.assertEqual(self.offer1.status, 'accepted')
        
        # Check that other offers were rejected
        self.offer2.refresh_from_db()
        self.assertEqual(self.offer2.status, 'rejected')
        
        # Check that notifications were sent
        self.assertTrue(mock_notification.called)
        self.assertEqual(mock_notification.call_count, 3)  # To accepted tech, rejected tech, client
    
    @patch('orders.views.Notification.objects.create')
    def test_admin_can_accept_offer_for_any_order(self, mock_notification):
        """Test that admins can accept offers for any order."""
        url = reverse('orders:order-accept-offer', kwargs={
            'pk': self.available_order.pk,
            'offer_id': self.offer2.offer_id
        })
        response = self.admin_client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh from database
        self.available_order.refresh_from_db()
        self.offer2.refresh_from_db()
        
        # Check that order was assigned to the accepted offer's technician
        self.assertEqual(self.available_order.technician_user, self.technician_user2)
        self.assertEqual(self.offer2.status, 'accepted')
    
    def test_technician_cannot_accept_offers(self):
        """Test that technicians cannot accept offers."""
        url = reverse('orders:order-accept-offer', kwargs={
            'pk': self.available_order.pk,
            'offer_id': self.offer1.offer_id
        })
        response = self.tech1_client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_returns_404_for_nonexistent_order(self):
        """Test that 404 is returned for non-existent orders."""
        url = reverse('orders:order-accept-offer', kwargs={
            'pk': 99999,
            'offer_id': self.offer1.offer_id
        })
        response = self.client_api.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_returns_404_for_nonexistent_offer(self):
        """Test that 404 is returned for offers that don't belong to the order."""
        url = reverse('orders:order-accept-offer', kwargs={
            'pk': self.available_order.pk,
            'offer_id': 99999
        })
        response = self.client_api.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UserTechniciansBrowseTests(BaseTestCase):
    """Test UserViewSet.technicians endpoint for browsing technicians."""
    
    def test_public_can_view_verified_technicians(self):
        """Test that anyone can browse verified technicians."""
        url = reverse('users:public_user-list')
        response = self.anonymous_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Only verified technicians
        
        # Check that only verified technicians are returned
        technician_ids = [tech['user_id'] for tech in response.data['results']]
        self.assertIn(self.technician_user1.user_id, technician_ids)
        self.assertIn(self.technician_user2.user_id, technician_ids)
        self.assertNotIn(self.technician_user3.user_id, technician_ids)
    
    def test_technicians_sorted_by_rating(self):
        """Test that technicians are sorted by rating and job completion count."""
        url = reverse('users:public_user-list')
        response = self.anonymous_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        technicians = response.data['results']
        
        # tech1 has rating 4.5, tech2 has rating 4.2
        self.assertEqual(technicians[0]['user_id'], self.technician_user1.user_id)
        self.assertEqual(technicians[1]['user_id'], self.technician_user2.user_id)
    
    def test_filter_by_specialization(self):
        """Test filtering technicians by specialization."""
        url = f"{reverse('users:public_user-list')}?specialization=Plumbing"
        response = self.anonymous_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['user_id'], self.technician_user1.user_id)
    
    def test_filter_by_location(self):
        """Test filtering technicians by location."""
        # Set addresses for technicians
        self.technician_user1.address = "Cairo, Egypt"
        self.technician_user1.save()
        
        self.technician_user2.address = "Alexandria, Egypt"
        self.technician_user2.save()
        
        url = f"{reverse('users:public_user-list')}?location=Cairo"
        response = self.anonymous_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['user_id'], self.technician_user1.user_id)
    
    def test_filter_by_minimum_rating(self):
        """Test filtering technicians by minimum rating."""
        url = f"{reverse('users:public_user-list')}?min_rating=4.3"
        response = self.anonymous_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['user_id'], self.technician_user1.user_id)
    
    def test_invalid_rating_filter_ignored(self):
        """Test that invalid rating filters are ignored."""
        url = f"{reverse('users:public_user-list')}?min_rating=invalid"
        response = self.anonymous_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # All technicians returned
    
    def test_authenticated_user_can_browse_technicians(self):
        """Test that authenticated users can also browse technicians."""
        url = reverse('users:public_user-list')
        response = self.client_api.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)


class UserTechnicianDetailTests(BaseTestCase):
    """Test UserViewSet.technician_detail endpoint."""
    
    def test_public_can_view_technician_details(self):
        """Test that anyone can view detailed technician information."""
        url = reverse('users:public_user_profile', kwargs={'pk': self.technician_user1.user_id})
        response = self.anonymous_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.technician_user1.user_id)
        self.assertEqual(response.data['specialization'], 'Plumbing')
        self.assertEqual(response.data['overall_rating'], 4.5)
    
    def test_returns_404_for_nonexistent_technician(self):
        """Test that 404 is returned for non-existent technicians."""
        url = reverse('users:public_user_profile', kwargs={'pk': 99999})
        response = self.anonymous_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_returns_404_for_unverified_technician(self):
        """Test that 404 is returned for unverified technicians."""
        url = reverse('users:public_user_profile', kwargs={'pk': self.technician_user3.user_id})
        response = self.anonymous_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_returns_404_for_client_user(self):
        """Test that 404 is returned when trying to view a client as technician."""
        url = reverse('users:public_user_profile', kwargs={'pk': self.client_user.user_id})
        response = self.anonymous_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProjectOfferCreateTests(BaseTestCase):
    """Test ProjectOfferViewset create functionality with notifications."""
    
    @patch('orders.views.Notification.objects.create')
    def test_technician_can_create_offer_with_notification(self, mock_notification):
        """Test that technicians can create offers and notifications are sent."""
        # Create a new order for this test
        new_order = Order.objects.create(
            service=self.plumbing_service,
            client_user=self.client_user,
            order_type='service_request',
            problem_description='New plumbing job',
            requested_location='321 Pine St, Cairo',
            scheduled_date=date(2025, 12, 5),
            scheduled_time_start='10:00',
            scheduled_time_end='12:00',
            creation_timestamp=date(2025, 11, 27),
            order_status='pending'
        )
        
        url = reverse('orders:projectoffer-list')
        data = {
            'order': new_order.order_id,
            'offered_price': 200.00,
            'offer_description': 'Expert plumbing service with warranty'
        }
        
        # Debug output to see what's happening
        print(f"DEBUG: Attempting to create offer with data: {data}")
        print(f"DEBUG: Technician user: {self.technician_user1.email}")
        print(f"DEBUG: Order exists: {new_order.order_id}")
        
        response = self.tech1_client.post(url, data)
        
        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response content: {response.content.decode()}")
        
        # Instead of asserting immediately, let's see what the error is
        if response.status_code != status.HTTP_201_CREATED:
            print(f"DEBUG: Full response data: {response.data}")
            print(f"DEBUG: Response headers: {response.headers}")
            
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['offered_price']), 200.00)
        
        # Check that notification was sent to client
        mock_notification.assert_called_once_with(
            user=self.client_user,
            notification_type='new_offer',
            title='New Offer Received',
            message=f'A new offer has been made for your order #{new_order.order_id}.',
            related_order=new_order
        )
    
    def test_technician_cannot_create_offer_for_another_technician(self):
        """Test that technicians cannot create offers for other technicians."""
        url = reverse('orders:projectoffer-list')
        data = {
            'order': self.available_order.order_id,
            'technician_user': self.technician_user2.user_id,  # Different technician
            'offered_price': 150.00,
            'offer_description': 'Offer for someone else'
        }
        response = self.tech1_client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_client_cannot_create_offers(self):
        """Test that clients cannot create project offers."""
        url = reverse('orders:projectoffer-list')
        data = {
            'order': self.available_order.order_id,
            'offered_price': 150.00,
            'offer_description': 'Client trying to create offer'
        }
        response = self.client_api.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class NotificationTests(BaseTestCase):
    """Test that notifications are properly created for various scenarios."""
    
    @patch('notifications.utils.create_notification')
    def test_notification_sent_when_offer_created(self, mock_create_notification):
        """Test that notifications are sent when offers are created."""
        new_order = Order.objects.create(
            service=self.plumbing_service,
            client_user=self.client_user,
            order_type='service_request',
            problem_description='Test order',
            requested_location='654 Maple Ave, Cairo',
            scheduled_date=date(2025, 12, 6),
            scheduled_time_start='10:00',
            scheduled_time_end='12:00',
            creation_timestamp=date(2025, 11, 27),
            order_status='pending'
        )
        
        url = reverse('orders:projectoffer-list')
        data = {
            'order': new_order.order_id,
            'offered_price': 100.00,
            'offer_description': 'Test offer'
        }
        response = self.tech1_client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_create_notification.assert_called_once()
    
    @patch('notifications.utils.create_notification')
    def test_notifications_sent_when_offer_accepted(self, mock_create_notification):
        """Test that proper notifications are sent when offers are accepted."""
        url = reverse('orders:order-accept-offer', kwargs={
            'order_id': self.available_order.order_id,
            'offer_id': self.offer1.offer_id
        })
        response = self.client_api.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have sent 3 notifications (to accepted tech, rejected tech, client)
        self.assertEqual(mock_create_notification.call_count, 3)
        
        # Check the calls
        calls = mock_create_notification.call_args_list
        
        # First call - to accepted technician
        self.assertEqual(calls[0][1]['user'], self.technician_user1)
        self.assertEqual(calls[0][1]['notification_type'], 'offer_accepted')
        
        # Second call - to rejected technician
        self.assertEqual(calls[1][1]['user'], self.technician_user2)
        self.assertEqual(calls[1][1]['notification_type'], 'offer_rejected')
        
        # Third call - to client
        self.assertEqual(calls[2][1]['user'], self.client_user)
        self.assertEqual(calls[2][1]['notification_type'], 'offer_accepted')


class EdgeCaseTests(BaseTestCase):
    """Test edge cases and error handling."""
    
    def test_available_for_offer_with_no_available_orders(self):
        """Test available_for_offer when no orders are available."""
        # Delete all available orders
        Order.objects.all().delete()
        
        url = reverse('orders:order-available-for-offer')
        response = self.tech1_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_offers_endpoint_with_no_offers(self):
        """Test offers endpoint when order has no offers."""
        # Create order with no offers
        empty_order = Order.objects.create(
            service=self.plumbing_service,
            client_user=self.client_user,
            order_type='service_request',
            problem_description='Order with no offers',
            requested_location='987 Cedar St, Alexandria',
            scheduled_date=date(2025, 12, 7),
            scheduled_time_start='10:00',
            scheduled_time_end='12:00',
            creation_timestamp=date(2025, 11, 27),
            order_status='pending'
        )
        
        url = reverse('orders:order-offers', kwargs={'pk': empty_order.pk})
        response = self.client_api.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_browse_technicians_with_no_verified_technicians(self):
        """Test browsing technicians when no verified technicians exist."""
        # Unverify all technicians
        self.technician_user1.verification_status = 'rejected'
        self.technician_user1.save()
        self.technician_user2.verification_status = 'rejected'
        self.technician_user2.save()
        
        url = reverse('users:public_user-list')
        response = self.anonymous_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_accept_already_accepted_offer(self):
        """Test accepting an offer that is already accepted."""
        # First accept the offer
        url = reverse('orders:order-accept-offer', kwargs={
            'pk': self.available_order.pk,
            'offer_id': self.offer1.offer_id
        })
        self.client_api.post(url)
        
        # Now try to accept it again
        response = self.client_api.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Should still work
        self.assertEqual(response.data['message'], 'Offer accepted successfully.')


class PermissionIntegrationTests(BaseTestCase):
    """Test that permissions work correctly across different user types."""
    
    def test_all_endpoints_require_authentication_except_public_technician_browse(self):
        """Test that only technician browsing is publicly accessible."""
        # Test order list - should require auth
        response = self.anonymous_client.get(reverse('orders:order-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test project offers list - should require auth
        response = self.anonymous_client.get(reverse('orders:projectoffer-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test technicians browse - should be public
        response = self.anonymous_client.get(reverse('users:public_user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test technician detail - should be public
        url = reverse('users:public_user_profile', kwargs={'pk': self.technician_user1.user_id})
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_cross_role_access_restrictions(self):
        """Test that users cannot access other roles' data."""
        # Client tries to access available orders
        url = reverse('orders:order-available-for-offer')
        response = self.client_api.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Technician tries to view offers for someone else's order
        url = reverse('orders:order-offers', kwargs={'pk': self.available_order.pk})
        response = self.tech1_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Technician tries to accept offers
        url = reverse('orders:order-accept-offer', kwargs={
            'pk': self.available_order.pk,
            'offer_id': self.offer1.offer_id
        })
        response = self.tech1_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ClientMakeOfferToTechnicianTests(BaseTestCase):
    """Test UserViewSet.make_offer_to_technician endpoint."""

    @patch('users.views.user_views.Notification.objects.create')
    def test_client_can_make_offer_to_technician_with_notification(self, mock_notification):
        """Test that a client can make a direct offer to a verified technician, creating an order and an offer."""
        url = reverse('users:user-make-offer-to-technician', kwargs={'pk': self.technician_user1.user_id})
        data = {
            'service_id': self.plumbing_service.service_id,
            'offered_price': 250.00,
            'problem_description': 'Direct hire for fixing a broken pipe.',
            'requested_location': '777 Test Street, Cairo',
            'scheduled_date': '2025-12-30',
            'scheduled_time_start': '09:00',
            'scheduled_time_end': '13:00',
            'offer_description': 'My direct offer for pipe repair.'
        }
        response = self.client_api.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Offer sent to technician successfully.')
        self.assertIn('order', response.data)
        self.assertIn('offer', response.data)

        order_data = response.data['order']
        offer_data = response.data['offer']

        # Verify Order creation
        self.assertEqual(order_data['client_user'], self.client_user.user_id)
        self.assertEqual(order_data['technician_user'], None) # Not yet assigned
        self.assertEqual(order_data['order_status'], 'awaiting_technician_response')
        self.assertEqual(order_data['order_type'], 'direct_hire')

        # Verify ProjectOffer creation
        self.assertEqual(offer_data['order'], order_data['order_id'])
        self.assertEqual(offer_data['technician_user']['user_id'], self.technician_user1.user_id)
        self.assertEqual(float(offer_data['offered_price']), 250.00)
        self.assertEqual(offer_data['status'], 'pending')
        self.assertEqual(offer_data['offer_initiator'], 'client')

        # Verify notification sent to technician
        mock_notification.assert_called_once_with(
            user=self.technician_user1,
            notification_type='new_client_offer',
            title='New Direct Offer Received',
            message=f'Client {self.client_user.get_full_name()} has made a direct offer for order #{order_data["order_id"]}.',
            related_order=Order.objects.get(order_id=order_data['order_id']),
            related_offer=ProjectOffer.objects.get(offer_id=offer_data['offer_id'])
        )
    
    def test_client_cannot_make_offer_to_unverified_technician(self):
        """Test that a client cannot make an offer to an unverified technician."""
        url = reverse('users:user-make-offer-to-technician', kwargs={'pk': self.technician_user3.user_id})
        data = {
            'service_id': self.plumbing_service.service_id,
            'offered_price': 100.00,
            'problem_description': 'Offer to unverified tech.',
            'requested_location': 'Unknown',
            'scheduled_date': '2025-12-30',
            'scheduled_time_start': '09:00',
            'scheduled_time_end': '10:00'
        }
        response = self.client_api.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_technician_cannot_make_client_offer(self):
        """Test that a technician cannot use the client make offer endpoint."""
        url = reverse('users:user-make-offer-to-technician', kwargs={'pk': self.technician_user1.user_id})
        data = {
            'service_id': self.plumbing_service.service_id,
            'offered_price': 100.00,
            'problem_description': 'Tech trying to make offer.',
            'requested_location': 'Unknown',
            'scheduled_date': '2025-12-30',
            'scheduled_time_start': '09:00',
            'scheduled_time_end': '10:00'
        }
        response = self.tech1_client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_anonymous_user_cannot_make_client_offer(self):
        """Test that an anonymous user cannot make a client offer."""
        url = reverse('users:user-make-offer-to-technician', kwargs={'pk': self.technician_user1.user_id})
        data = {
            'service_id': self.plumbing_service.service_id,
            'offered_price': 100.00,
            'problem_description': 'Anon trying to make offer.',
            'requested_location': 'Unknown',
            'scheduled_date': '2025-12-30',
            'scheduled_time_start': '09:00',
            'scheduled_time_end': '10:00'
        }
        response = self.anonymous_client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class TechnicianRespondToClientOfferTests(BaseTestCase):
    """Test UserViewSet.respond_to_client_offer endpoint."""

    def setUp(self):
        super().setUp()
        # Create an order and a client-initiated offer for technician1
        self.client_offer_order = Order.objects.create(
            service=self.plumbing_service,
            client_user=self.client_user,
            order_type='direct_hire',
            problem_description='Client-initiated job',
            requested_location='Client Offer Location',
            scheduled_date=date(2026, 1, 1),
            scheduled_time_start='10:00',
            scheduled_time_end='12:00',
            creation_timestamp=date(2025, 11, 28),
            order_status='awaiting_technician_response'
        )
        self.client_offer_to_tech1 = ProjectOffer.objects.create(
            order=self.client_offer_order,
            technician_user=self.technician_user1,
            offered_price=300.00,
            offer_description='Client offers this much.',
            offer_date=date(2025, 11, 28),
            status='pending',
            offer_initiator='client'
        )
        
        # Create another client-initiated offer for technician2, which will be rejected
        self.client_offer_to_tech2_order = Order.objects.create(
            service=self.electrical_service,
            client_user=self.client_user,
            order_type='direct_hire',
            problem_description='Client-initiated electrical job',
            requested_location='Another Client Offer Location',
            scheduled_date=date(2026, 1, 2),
            scheduled_time_start='14:00',
            scheduled_time_end='16:00',
            creation_timestamp=date(2025, 11, 28),
            order_status='awaiting_technician_response'
        )
        self.client_offer_to_tech2 = ProjectOffer.objects.create(
            order=self.client_offer_to_tech2_order,
            technician_user=self.technician_user2,
            offered_price=400.00,
            offer_description='Client offers for electrical.',
            offer_date=date(2025, 11, 28),
            status='pending',
            offer_initiator='client'
        )

    @patch('users.views.user_views.Notification.objects.create')
    def test_technician_can_accept_client_offer(self, mock_notification):
        """Test that a technician can accept a client's direct offer."""
        url = reverse('users:user-respond-to-client-offer', kwargs={
            'pk': self.technician_user1.user_id,
            'offer_id': self.client_offer_to_tech1.offer_id
        })
        data = {'action': 'accept'}
        response = self.tech1_client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Offer accepted successfully.')
        self.assertIn('offer', response.data)
        self.assertIn('order_status', response.data)
        self.assertEqual(response.data['order_status'], 'accepted')

        self.client_offer_order.refresh_from_db()
        self.client_offer_to_tech1.refresh_from_db()

        self.assertEqual(self.client_offer_order.technician_user, self.technician_user1)
        self.assertEqual(self.client_offer_order.order_status, 'accepted')
        self.assertEqual(self.client_offer_to_tech1.status, 'accepted')

        # Verify notification to client
        mock_notification.assert_called_once_with(
            user=self.client_user,
            notification_type='client_offer_accepted',
            title='Your Direct Offer Was Accepted!',
            message=f'Technician {self.technician_user1.get_full_name()} has accepted your direct offer for order #{self.client_offer_order.order_id}.',
            related_order=self.client_offer_order,
            related_offer=self.client_offer_to_tech1
        )
    
    @patch('users.views.user_views.Notification.objects.create')
    def test_technician_can_reject_client_offer(self, mock_notification):
        """Test that a technician can reject a client's direct offer."""
        url = reverse('users:user-respond-to-client-offer', kwargs={
            'pk': self.technician_user2.user_id,
            'offer_id': self.client_offer_to_tech2.offer_id
        })
        data = {'action': 'reject', 'rejection_reason': 'Not available on that date.'}
        response = self.tech2_client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Offer rejected successfully.')
        self.assertIn('offer', response.data)
        self.assertNotIn('order_status', response.data) # Order status not changed on rejection

        self.client_offer_order.refresh_from_db() # Should not be affected
        self.client_offer_to_tech2.refresh_from_db()

        self.assertEqual(self.client_offer_to_tech2.status, 'rejected')
        self.assertIn('(Rejected: Not available on that date.)', self.client_offer_to_tech2.offer_description)
        self.assertEqual(self.client_offer_to_tech2_order.order_status, 'awaiting_technician_response') # Order status remains

        # Verify notification to client
        mock_notification.assert_called_once_with(
            user=self.client_user,
            notification_type='client_offer_rejected',
            title='Your Direct Offer Was Rejected',
            message=f'Technician {self.technician_user2.get_full_name()} has rejected your direct offer for order #{self.client_offer_to_tech2_order.order_id}. Reason: Not available on that date.',
            related_order=self.client_offer_to_tech2_order,
            related_offer=self.client_offer_to_tech2
        )

    def test_technician_cannot_respond_to_non_pending_offer(self):
        """Test that a technician cannot respond to an offer that is not pending."""
        self.client_offer_to_tech1.status = 'accepted' # Mark as accepted already
        self.client_offer_to_tech1.save()

        url = reverse('users:user-respond-to-client-offer', kwargs={
            'pk': self.technician_user1.user_id,
            'offer_id': self.client_offer_to_tech1.offer_id
        })
        data = {'action': 'accept'}
        response = self.tech1_client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Not Found because only pending offers are queried

    def test_technician_cannot_respond_to_offer_not_made_to_them(self):
        """Test that a technician cannot respond to an offer not directed at them."""
        # Tech2 tries to respond to Tech1's offer
        url = reverse('users:user-respond-to-client-offer', kwargs={
            'pk': self.technician_user2.user_id,
            'offer_id': self.client_offer_to_tech1.offer_id
        })
        data = {'action': 'accept'}
        response = self.tech2_client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Not Found as it's not their offer

    def test_client_cannot_respond_to_offer(self):
        """Test that a client cannot respond to an offer (it's a technician action)."""
        url = reverse('users:user-respond-to-client-offer', kwargs={
            'pk': self.technician_user1.user_id,
            'offer_id': self.client_offer_to_tech1.offer_id
        })
        data = {'action': 'accept'}
        response = self.client_api.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_respond_to_offer(self):
        """Test that an anonymous user cannot respond to an offer."""
        url = reverse('users:user-respond-to-client-offer', kwargs={
            'pk': self.technician_user1.user_id,
            'offer_id': self.client_offer_to_tech1.offer_id
        })
        data = {'action': 'accept'}
        response = self.anonymous_client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

# Test data factory functions for easier test setup
class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_client_user(email='client@test.com'):
        """Create a test client user."""
        return User.objects.create_user(
            email=email,
            password='clientpass',
            first_name='Test',
            last_name='Client',
            user_type_name='client'
        )
    
    @staticmethod
    def create_technician_user(email='tech@test.com', specialization='General', rating=4.0):
        """Create a test technician user."""
        return User.objects.create_user(
            email=email,
            password='techpass',
            first_name='Test',
            last_name='Technician',
            user_type_name='technician',
            verification_status='verified',
            account_status='active',
            specialization=specialization,
            overall_rating=rating,
            num_jobs_completed=5
        )
    
    @staticmethod
    def create_service(name='General Service'):
        """Create a test service."""
        category, _ = ServiceCategory.objects.get_or_create(category_name='Test Category')
        return Service.objects.create(
            category=category,
            service_name=name,
            description=f'{name} description',
            service_type='General',
            base_inspection_fee=50.00
        )
    
    @staticmethod
    def create_order(client, service, status='pending'):
        """Create a test order."""
        return Order.objects.create(
            service=service,
            client_user=client,
            order_type='service_request',
            problem_description=f'Test {service.service_name} order',
            requested_location='Test Location, Cairo',
            scheduled_date=date(2025, 12, 1),
            scheduled_time_start='10:00',
            scheduled_time_end='12:00',
            creation_timestamp=date(2025, 11, 27),
            order_status=status
        )
    
    @staticmethod
    def create_offer(order, technician, price=100.00):
        """Create a test project offer."""
        return ProjectOffer.objects.create(
            order=order,
            technician_user=technician,
            offered_price=price,
            offer_description=f'Offer for {order.problem_description}',
            offer_date=date(2025, 11, 27),
            status='pending'
        )
