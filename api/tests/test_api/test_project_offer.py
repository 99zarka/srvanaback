from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import ProjectOffer, User, Order, Service, ServiceCategory
from api.models.users import UserType
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction

class ProjectOfferTests(APITestCase):
    @transaction.atomic
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
            username='techuser',
            email='technician@example.com',
            password='password123',
            user_type_name=self.technician_usertype.user_type_name
        )
        self.other_technician_user = User.objects.create_user(
            username='othertech',
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
        self.order_client_user = Order.objects.create(
            client_user=self.client_user,
            service=self.service,
            order_type='Repair',
            problem_description='Fix something for client user',
            requested_location='Someplace',
            scheduled_date='2025-01-01',
            scheduled_time_start='09:00',
            scheduled_time_end='10:00',
            order_status='pending',
            creation_timestamp='2025-01-01'
        )
        self.order_other_client_user = Order.objects.create(
            client_user=self.other_client_user,
            service=self.service,
            order_type='Repair',
            problem_description='Fix something for other client user',
            requested_location='Other Place',
            scheduled_date='2025-01-02',
            scheduled_time_start='11:00',
            scheduled_time_end='12:00',
            order_status='pending',
            creation_timestamp='2025-01-02'
        )

        self.project_offer_data = {
            'order': self.order_client_user.order_id,
            'technician_user': self.technician_user.user_id,
            'offered_price': 150.00,
            'offer_description': 'Offer description',
            'status': 'pending',
            'offer_date': '2025-01-01'
        }
        self.project_offer_tech_user = ProjectOffer.objects.create(
            order=self.order_client_user,
            technician_user=self.technician_user,
            offered_price=120.00,
            offer_description='Existing offer by tech user',
            status='accepted',
            offer_date='2025-01-01'
        )
        self.project_offer_other_tech_user = ProjectOffer.objects.create(
            order=self.order_other_client_user,
            technician_user=self.other_technician_user,
            offered_price=130.00,
            offer_description='Existing offer by other tech user',
            status='pending',
            offer_date='2025-01-02'
        )

        self.list_url = reverse('projectoffer-list')
        self.detail_url_tech_user = reverse('projectoffer-detail', args=[self.project_offer_tech_user.offer_id])
        self.detail_url_other_tech_user = reverse('projectoffer-detail', args=[self.project_offer_other_tech_user.offer_id])

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    # --- Unauthenticated User Tests ---
    def test_unauthenticated_create_project_offer(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, self.project_offer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_list_project_offers(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_retrieve_project_offer(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.detail_url_tech_user)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_update_project_offer(self):
        updated_data = {'status': 'accepted'}
        response = self.client.patch(self.detail_url_tech_user, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_delete_project_offer(self):
        response = self.client.delete(self.detail_url_tech_user)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Client User Tests (Owner/Related) ---
    def test_client_create_project_offer_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.post(self.list_url, self.project_offer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_list_own_order_project_offers(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Client sees only offers for their orders
        self.assertEqual(response.data[0]['offered_price'], '120.00')

    def test_client_retrieve_own_order_project_offer(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url_tech_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['offered_price'], '120.00')

    def test_client_retrieve_other_order_project_offer_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url_other_tech_user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Client cannot retrieve offers for other client's orders

    def test_client_update_project_offer_forbidden(self):
        client = self.get_auth_client(self.client_user)
        updated_data = {'status': 'accepted'}
        response = client.patch(self.detail_url_tech_user, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_delete_project_offer_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url_tech_user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Technician User Tests (Owner) ---
    def test_technician_create_project_offer(self):
        client = self.get_auth_client(self.technician_user)
        new_order = Order.objects.create(
            client_user=self.client_user,
            service=self.service,
            order_type='Repair',
            problem_description='New order for tech offer',
            requested_location='New Place',
            scheduled_date='2025-01-03',
            scheduled_time_start='13:00',
            scheduled_time_end='14:00',
            order_status='pending',
            creation_timestamp='2025-01-03'
        )
        new_offer_data = self.project_offer_data.copy()
        new_offer_data['order'] = new_order.order_id
        response = client.post(self.list_url, new_offer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProjectOffer.objects.count(), 3)
        self.assertEqual(response.data['offered_price'], '150.00')

    def test_technician_list_own_project_offers(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only offers by this technician
        self.assertEqual(response.data[0]['offered_price'], '120.00')

    def test_technician_retrieve_own_project_offer(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.detail_url_tech_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['offered_price'], '120.00')

    def test_technician_update_own_project_offer(self):
        client = self.get_auth_client(self.technician_user)
        updated_data = {'offer_description': 'Updated offer description by tech', 'offered_price': 160.00}
        response = client.patch(self.detail_url_tech_user, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project_offer_tech_user.refresh_from_db()
        self.assertEqual(self.project_offer_tech_user.offered_price, 160.00)

    def test_technician_delete_own_project_offer(self):
        client = self.get_auth_client(self.technician_user)
        response = client.delete(self.detail_url_tech_user)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ProjectOffer.objects.filter(offer_id=self.project_offer_tech_user.offer_id).exists(), False)

    # --- Technician User Tests (Non-Owner) ---
    def test_technician_retrieve_other_project_offer_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.detail_url_other_tech_user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Tech cannot retrieve other tech's offer

    def test_technician_update_other_project_offer_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        updated_data = {'status': 'accepted'}
        response = client.patch(self.detail_url_other_tech_user, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_technician_delete_other_project_offer_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.delete(self.detail_url_other_tech_user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Admin User Tests ---
    def test_admin_create_project_offer(self):
        client = self.get_auth_client(self.admin_user)
        new_order = Order.objects.create(
            client_user=self.client_user,
            service=self.service,
            order_type='Repair',
            problem_description='Admin created order',
            requested_location='Admin Place',
            scheduled_date='2025-01-04',
            scheduled_time_start='15:00',
            scheduled_time_end='16:00',
            order_status='pending',
            creation_timestamp='2025-01-04'
        )
        admin_offer_data = self.project_offer_data.copy()
        admin_offer_data['order'] = new_order.order_id
        response = client.post(self.list_url, admin_offer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProjectOffer.objects.count(), 3)

    def test_admin_list_all_project_offers(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Admin sees all offers

    def test_admin_retrieve_any_project_offer(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.detail_url_tech_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['offered_price'], '120.00')

    def test_admin_update_any_project_offer(self):
        client = self.get_auth_client(self.admin_user)
        updated_data = {'status': 'rejected', 'offered_price': 100.00}
        response = client.patch(self.detail_url_tech_user, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project_offer_tech_user.refresh_from_db()
        self.assertEqual(self.project_offer_tech_user.status, 'rejected')

    def test_admin_delete_any_project_offer(self):
        client = self.get_auth_client(self.admin_user)
        response = client.delete(self.detail_url_tech_user)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ProjectOffer.objects.count(), 1) # One deleted
