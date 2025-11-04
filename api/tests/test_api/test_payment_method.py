from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import PaymentMethod, User
from api.models.users import UserType
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

class PaymentMethodTests(APITestCase):
    def setUp(self):
        self.client_usertype = UserType.objects.create(user_type_name='client')
        self.technician_usertype = UserType.objects.create(user_type_name='technician')
        self.admin_usertype = UserType.objects.create(user_type_name='admin')

        self.client_user = User.objects.create_user(
            username='clientuser',
            email='client@example.com',
            password='password123',
            user_type=self.client_usertype
        )
        self.other_client_user = User.objects.create_user(
            username='otherclient',
            email='other@example.com',
            password='password123',
            user_type=self.client_usertype
        )
        self.technician_user = User.objects.create_user(
            username='techuser',
            email='technician@example.com',
            password='password123',
            user_type=self.technician_usertype
        )
        self.admin_user = User.objects.create(
            email="admin@example.com",
            username="adminuser",
            password=make_password("adminpassword123"),
            first_name="Admin",
            last_name="User",
            phone_number="0987654321",
            address="456 Admin Ave",
            user_type=self.admin_usertype,
            is_staff=True,
            is_superuser=True
        )

        self.payment_method_data = {
            'user': self.client_user.user_id,
            'card_type': 'Visa',
            'last_four_digits': '1111',
            'expiration_date': '12/25',
            'card_holder_name': 'Client User',
            'is_default': True
        }
        self.payment_method = PaymentMethod.objects.create(
            user=self.client_user,
            card_type='MasterCard',
            last_four_digits='2222',
            expiration_date='10/24',
            card_holder_name='Client User',
            is_default=False
        )
        self.other_payment_method = PaymentMethod.objects.create(
            user=self.other_client_user,
            card_type='Amex',
            last_four_digits='3333',
            expiration_date='01/26',
            card_holder_name='Other Client User',
            is_default=True
        )

        self.list_url = reverse('paymentmethod-list')
        self.detail_url = reverse('paymentmethod-detail', args=[self.payment_method.id])
        self.other_detail_url = reverse('paymentmethod-detail', args=[self.other_payment_method.id])

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    # --- Unauthenticated User Tests ---
    def test_unauthenticated_create_payment_method(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, self.payment_method_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_list_payment_methods(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_retrieve_payment_method(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_update_payment_method(self):
        updated_data = {'is_default': False}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_delete_payment_method(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Client User Tests (Owner) ---
    def test_client_create_payment_method(self):
        client = self.get_auth_client(self.client_user)
        response = client.post(self.list_url, self.payment_method_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PaymentMethod.objects.filter(user=self.client_user).count(), 2)
        self.assertEqual(response.data['card_type'], 'Visa')

    def test_client_list_own_payment_methods(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only payment methods belonging to the authenticated user
        self.assertEqual(response.data[0]['card_type'], 'MasterCard')

    def test_client_retrieve_own_payment_method(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['card_type'], 'MasterCard')

    def test_client_update_own_payment_method(self):
        client = self.get_auth_client(self.client_user)
        updated_data = {'is_default': True, 'expiration_date': '11/26'}
        response = client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment_method.refresh_from_db()
        self.assertEqual(self.payment_method.is_default, True)

    def test_client_delete_own_payment_method(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PaymentMethod.objects.filter(user=self.client_user).count(), 0)

    # --- Client User Tests (Non-Owner) ---
    def test_client_create_payment_method_for_other_user_forbidden(self):
        client = self.get_auth_client(self.client_user)
        other_user_payment_data = self.payment_method_data.copy()
        other_user_payment_data['user'] = self.other_client_user.user_id
        response = client.post(self.list_url, other_user_payment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_list_other_payment_methods_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Should not find other user's payment method

    def test_client_retrieve_other_payment_method_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_client_update_other_payment_method_forbidden(self):
        client = self.get_auth_client(self.client_user)
        updated_data = {'is_default': True}
        response = client.patch(self.other_detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_client_delete_other_payment_method_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Admin User Tests ---
    def test_admin_create_payment_method(self):
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.list_url, self.payment_method_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PaymentMethod.objects.count(), 3) # 2 existing + 1 new
        self.assertEqual(response.data['card_type'], 'Visa')

    def test_admin_list_all_payment_methods(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Admin sees all payment methods

    def test_admin_retrieve_any_payment_method(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['card_type'], 'MasterCard')

    def test_admin_update_any_payment_method(self):
        client = self.get_auth_client(self.admin_user)
        updated_data = {'is_default': True, 'expiration_date': '11/26'}
        response = client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment_method.refresh_from_db()
        self.assertEqual(self.payment_method.is_default, True)

    def test_admin_delete_any_payment_method(self):
        client = self.get_auth_client(self.admin_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PaymentMethod.objects.count(), 1) # One deleted

    # --- Technician User Tests ---
    def test_technician_create_own_payment_method(self):
        client = self.get_auth_client(self.technician_user)
        tech_payment_data = self.payment_method_data.copy()
        tech_payment_data['user'] = self.technician_user.user_id
        response = client.post(self.list_url, tech_payment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PaymentMethod.objects.filter(user=self.technician_user).count(), 1)

    def test_technician_create_payment_method_for_other_user_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        other_user_payment_data = self.payment_method_data.copy()
        other_user_payment_data['user'] = self.client_user.user_id
        response = client.post(self.list_url, other_user_payment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_technician_list_own_payment_methods(self):
        # Create a payment method for the technician first
        PaymentMethod.objects.create(
            user=self.technician_user,
            card_type='Visa',
            last_four_digits='4444',
            expiration_date='05/27',
            card_holder_name='Technician User',
            is_default=True
        )
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], self.technician_user.user_id)

    def test_technician_retrieve_own_payment_method(self):
        # Create a payment method for the technician first
        tech_payment_method = PaymentMethod.objects.create(
            user=self.technician_user,
            card_type='Visa',
            last_four_digits='4444',
            expiration_date='05/27',
            card_holder_name='Technician User',
            is_default=True
        )
        detail_url_tech = reverse('paymentmethod-detail', args=[tech_payment_method.id])
        client = self.get_auth_client(self.technician_user)
        response = client.get(detail_url_tech)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.technician_user.user_id)

    def test_technician_retrieve_other_payment_method_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.detail_url) # client_user's payment method
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_technician_update_own_payment_method(self):
        # Create a payment method for the technician first
        tech_payment_method = PaymentMethod.objects.create(
            user=self.technician_user,
            card_type='Visa',
            last_four_digits='4444',
            expiration_date='05/27',
            card_holder_name='Technician User',
            is_default=True
        )
        detail_url_tech = reverse('paymentmethod-detail', args=[tech_payment_method.id])
        client = self.get_auth_client(self.technician_user)
        updated_data = {'is_default': False, 'expiration_date': '06/28'}
        response = client.patch(detail_url_tech, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tech_payment_method.refresh_from_db()
        self.assertEqual(tech_payment_method.is_default, False)

    def test_technician_update_other_payment_method_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        updated_data = {'is_default': True}
        response = client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_technician_delete_own_payment_method(self):
        # Create a payment method for the technician first
        tech_payment_method = PaymentMethod.objects.create(
            user=self.technician_user,
            card_type='Visa',
            last_four_digits='4444',
            expiration_date='05/27',
            card_holder_name='Technician User',
            is_default=True
        )
        detail_url_tech = reverse('paymentmethod-detail', args=[tech_payment_method.id])
        client = self.get_auth_client(self.technician_user)
        response = client.delete(detail_url_tech)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PaymentMethod.objects.filter(id=tech_payment_method.id).exists())

    def test_technician_delete_other_payment_method_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
