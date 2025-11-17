from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from .models import Review
from users.models import User, UserType
from services.models import Service, ServiceCategory
from orders.models import Order
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

class ReviewTests(APITestCase):
    def setUp(self):
        self.client_usertype = UserType.objects.create(user_type_name='client')
        self.technician_usertype = UserType.objects.create(user_type_name='technician')
        self.admin_usertype = UserType.objects.create(user_type_name='admin')

        self.client_user = User.objects.create_user(
            username='clientuser',
            email='client@example.com',
            password='password123',
            user_type_name=self.client_usertype.user_type_name
        )
        self.other_client_user = User.objects.create_user(
            username='otherclient',
            email='otherclient@example.com',
            password='password123',
            user_type_name=self.client_usertype.user_type_name
        )
        self.technician_user = User.objects.create_user(
            username='technicianuser',
            email='technician@example.com',
            password='password123',
            user_type_name=self.technician_usertype.user_type_name
        )
        self.other_technician_user = User.objects.create_user(
            username='othertechnician',
            email='othertech@example.com',
            password='password123',
            user_type_name=self.technician_usertype.user_type_name
        )
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            username="adminuser",
            password="adminpassword123",
            first_name="Admin",
            last_name="User",
            phone_number="0987654321",
            address="456 Admin Ave",
            user_type_name=self.admin_usertype.user_type_name,
        )

        self.service_category = ServiceCategory.objects.create(category_name='Electronics Repair')
        self.service = Service.objects.create(
            category=self.service_category,
            service_name='Test Service',
            description='Description for test service',
            service_type='Repair',
            base_inspection_fee=50.00
        )
        self.order_client_tech = Order.objects.create(
            client_user=self.client_user,
            technician_user=self.technician_user,
            service=self.service,
            order_type='Repair',
            problem_description='Broken screen for client/tech',
            requested_location='Client Home',
            scheduled_date='2025-01-01',
            scheduled_time_start='09:00',
            scheduled_time_end='10:00',
            order_status='completed',
            creation_timestamp='2025-01-01'
        )
        self.order_other_client_other_tech = Order.objects.create(
            client_user=self.other_client_user,
            technician_user=self.other_technician_user,
            service=self.service,
            order_type='Repair',
            problem_description='Broken screen for other client/tech',
            requested_location='Other Client Home',
            scheduled_date='2025-01-02',
            scheduled_time_start='11:00',
            scheduled_time_end='12:00',
            order_status='completed',
            creation_timestamp='2025-01-02'
        )

        self.review_client_tech = Review.objects.create(
            reviewer=self.client_user,
            technician=self.technician_user,
            order=self.order_client_tech,
            rating=4,
            comment='Good service from technician.'
        )
        self.review_other_client_other_tech = Review.objects.create(
            reviewer=self.other_client_user,
            technician=self.other_technician_user,
            order=self.order_other_client_other_tech,
            rating=5,
            comment='Excellent service from other technician.'
        )

        self.review_data = {
            'reviewer': self.client_user.pk,
            'technician': self.technician_user.pk,
            'order': self.order_client_tech.pk,
            'rating': 5,
            'comment': 'Excellent service!'
        }

        self.list_url = reverse('review-list')
        self.detail_url_client_tech = reverse('review-detail', args=[self.review_client_tech.id])
        self.other_detail_url = reverse('review-detail', args=[self.review_other_client_other_tech.id])

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    # --- Unauthenticated User Tests ---
    def test_unauthenticated_create_review(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, self.review_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_list_reviews(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_retrieve_review(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.detail_url_client_tech)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_update_review(self):
        updated_data = {'rating': 3}
        response = self.client.patch(self.detail_url_client_tech, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_delete_review(self):
        response = self.client.delete(self.detail_url_client_tech)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Client User Tests (Owner/Related) ---
    def test_client_create_review(self):
        client = self.get_auth_client(self.client_user)
        new_service = Service.objects.create(
            category=self.service_category,
            service_name='New Test Service',
            description='Description for new test service',
            service_type='Repair',
            base_inspection_fee=60.00
        )
        new_order = Order.objects.create(
            client_user=self.client_user,
            technician_user=self.technician_user,
            service=new_service,
            order_type='Repair',
            problem_description='Another broken screen',
            requested_location='Client New Home',
            scheduled_date='2025-01-03',
            scheduled_time_start='13:00',
            scheduled_time_end='14:00',
            order_status='completed',
            creation_timestamp='2025-01-03'
        )
        new_review_data = {
            'reviewer': self.client_user.pk,
            'technician': self.technician_user.pk,
            'order': new_order.pk,
            'rating': 5,
            'comment': 'Excellent service again!'
        }
        response = client.post(self.list_url, new_review_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 3)
        self.assertEqual(response.data['rating'], 5)

    def test_client_list_own_and_related_reviews(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only reviews where client_user is reviewer or related to their order
        self.assertEqual(response.data[0]['rating'], 4)

    def test_client_retrieve_own_review(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url_client_tech)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 4)

    def test_client_retrieve_other_client_review_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Client cannot retrieve other client's review

    def test_client_update_own_review(self):
        client = self.get_auth_client(self.client_user)
        updated_data = {'rating': 3, 'comment': 'Service was okay.'}
        response = client.patch(self.detail_url_client_tech, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review_client_tech.refresh_from_db()
        self.assertEqual(self.review_client_tech.rating, 3)

    def test_client_update_other_client_review_forbidden(self):
        client = self.get_auth_client(self.client_user)
        updated_data = {'rating': 1}
        response = client.patch(self.other_detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_client_delete_own_review(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url_client_tech)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Review.objects.filter(id=self.review_client_tech.id).exists(), False)

    def test_client_delete_other_client_review_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Technician User Tests (Related) ---
    def test_technician_create_review_as_client(self):
        client = self.get_auth_client(self.technician_user)
        new_service = Service.objects.create(
            category=self.service_category,
            service_name='Technician Client Service',
            description='Description for technician client service',
            service_type='Repair',
            base_inspection_fee=80.00
        )
        # Technician acts as a client to order a service from another technician
        technician_as_client_order = Order.objects.create(
            client_user=self.technician_user, # Technician is the client
            technician_user=self.other_technician_user, # Another technician provides the service
            service=new_service,
            order_type='Repair',
            problem_description='Technician ordered service',
            requested_location='Technician Home',
            scheduled_date='2025-01-05',
            scheduled_time_start='17:00',
            scheduled_time_end='18:00',
            order_status='completed',
            creation_timestamp='2025-01-05'
        )
        technician_review_data = {
            'reviewer': self.technician_user.pk,
            'technician': self.other_technician_user.pk,
            'order': technician_as_client_order.pk,
            'rating': 4,
            'comment': 'Good service from other technician as a client.'
        }
        response = client.post(self.list_url, technician_review_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 3) # Two initial reviews + one new review
        self.assertEqual(response.data['rating'], 4)

    def test_technician_list_reviews_they_made_and_received(self):
        # Create a review where technician_user is the reviewer (acting as a client)
        new_service = Service.objects.create(
            category=self.service_category,
            service_name='Technician Client Service 2',
            description='Description for technician client service 2',
            service_type='Repair',
            base_inspection_fee=85.00
        )
        technician_as_client_order_2 = Order.objects.create(
            client_user=self.technician_user,
            technician_user=self.other_technician_user,
            service=new_service,
            order_type='Repair',
            problem_description='Technician ordered service 2',
            requested_location='Technician Home 2',
            scheduled_date='2025-01-06',
            scheduled_time_start='19:00',
            scheduled_time_end='20:00',
            order_status='completed',
            creation_timestamp='2025-01-06'
        )
        Review.objects.create(
            reviewer=self.technician_user,
            technician=self.other_technician_user,
            order=technician_as_client_order_2,
            rating=3,
            comment='Okay service from other technician.'
        )

        client = self.get_auth_client(self.technician_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # One review received, one review made
        # Check if both types of reviews are present
        ratings = [review['rating'] for review in response.data]
        self.assertIn(4, ratings) # Review received (review_client_tech)
        self.assertIn(3, ratings) # Review made by technician_user

    def test_technician_retrieve_review_they_made_or_received(self):
        # Create a review where technician_user is the reviewer (acting as a client)
        new_service = Service.objects.create(
            category=self.service_category,
            service_name='Technician Client Service 3',
            description='Description for technician client service 3',
            service_type='Repair',
            base_inspection_fee=90.00
        )
        technician_as_client_order_3 = Order.objects.create(
            client_user=self.technician_user,
            technician_user=self.other_technician_user,
            service=new_service,
            order_type='Repair',
            problem_description='Technician ordered service 3',
            requested_location='Technician Home 3',
            scheduled_date='2025-01-07',
            scheduled_time_start='21:00',
            scheduled_time_end='22:00',
            order_status='completed',
            creation_timestamp='2025-01-07'
        )
        review_made_by_technician = Review.objects.create(
            reviewer=self.technician_user,
            technician=self.other_technician_user,
            order=technician_as_client_order_3,
            rating=2,
            comment='Bad service from other technician.'
        )

        client = self.get_auth_client(self.technician_user)
        # Retrieve a review they received
        response_received = client.get(self.detail_url_client_tech)
        self.assertEqual(response_received.status_code, status.HTTP_200_OK)
        self.assertEqual(response_received.data['rating'], 4)

        # Retrieve a review they made
        response_made = client.get(reverse('review-detail', args=[review_made_by_technician.id]))
        self.assertEqual(response_made.status_code, status.HTTP_200_OK)
        self.assertEqual(response_made.data['rating'], 2)

    def test_technician_retrieve_other_technician_review_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_technician_update_review_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        updated_data = {'rating': 1}
        response = client.patch(self.detail_url_client_tech, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_technician_delete_review_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.delete(self.detail_url_client_tech)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Admin User Tests ---
    def test_admin_create_review(self):
        client = self.get_auth_client(self.admin_user)
        new_service = Service.objects.create(
            category=self.service_category,
            service_name='Admin Test Service',
            description='Description for admin test service',
            service_type='Repair',
            base_inspection_fee=70.00
        )
        admin_order = Order.objects.create(
            client_user=self.client_user,
            technician_user=self.technician_user,
            service=new_service,
            order_type='Repair',
            problem_description='Admin created order',
            requested_location='Admin Home',
            scheduled_date='2025-01-04',
            scheduled_time_start='15:00',
            scheduled_time_end='16:00',
            order_status='completed',
            creation_timestamp='2025-01-04'
        )
        admin_review_data = {
            'reviewer': self.client_user.pk,
            'technician': self.technician_user.pk,
            'order': admin_order.pk,
            'rating': 5,
            'comment': 'Admin created review!'
        }
        response = client.post(self.list_url, admin_review_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 3)

    def test_admin_list_all_reviews(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Admin sees all reviews

    def test_admin_retrieve_any_review(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.detail_url_client_tech)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 4)

    def test_admin_update_any_review(self):
        client = self.get_auth_client(self.admin_user)
        updated_data = {'rating': 1, 'comment': 'Admin updated comment.'}
        response = client.patch(self.detail_url_client_tech, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review_client_tech.refresh_from_db()
        self.assertEqual(self.review_client_tech.rating, 1)

    def test_admin_delete_any_review(self):
        client = self.get_auth_client(self.admin_user)
        response = client.delete(self.detail_url_client_tech)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Review.objects.count(), 1) # One deleted
