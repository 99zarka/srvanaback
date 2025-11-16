from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import Address, User
from api.models.users import UserType
from api.permissions import IsAdminUser, IsOwnerOrAdmin # Import necessary permissions

class AddressTests(APITestCase):
    def setUp(self):
        self.usertype_client = UserType.objects.create(user_type_name='client')
        self.usertype_admin = UserType.objects.create(user_type_name='admin')

        self.client_user = User.objects.create_user(
            username='clientuser',
            email='client@example.com',
            password='password123',
            user_type_name=self.usertype_client.user_type_name
        )
        self.other_client_user = User.objects.create_user(
            username='otherclient',
            email='other@example.com',
            password='password123',
            user_type_name=self.usertype_client.user_type_name
        )
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpassword',
            user_type_name=self.usertype_admin.user_type_name
        )

        self.address_data = {
            'user': self.client_user.user_id,
            'street_address': '123 Main St',
            'city': 'Anytown',
            'state': 'CA',
            'zip_code': '90210',
            'country': 'USA'
        }
        self.address = Address.objects.create(
            user=self.client_user,
            street_address='456 Oak Ave',
            city='Otherville',
            state='NY',
            zip_code='10001',
            country='USA'
        )
        self.other_address = Address.objects.create(
            user=self.other_client_user,
            street_address='789 Pine Ln',
            city='Another City',
            state='TX',
            zip_code='75001',
            country='USA'
        )
        self.list_url = reverse('address-list')
        self.detail_url = reverse('address-detail', args=[self.address.id])
        self.other_detail_url = reverse('address-detail', args=[self.other_address.id])

    def test_create_address(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(self.list_url, self.address_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Address.objects.count(), 3) # 2 existing + 1 new
        self.assertEqual(response.data['street_address'], '123 Main St')

    def test_create_address_unauthenticated(self):
        response = self.client.post(self.list_url, self.address_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_addresses(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only addresses belonging to the authenticated user

    def test_list_addresses_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_addresses_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Admin sees all addresses

    def test_retrieve_address(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['street_address'], '456 Oak Ave')

    def test_retrieve_address_unauthenticated(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_other_address_by_client(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Client cannot retrieve other's address

    def test_retrieve_address_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['street_address'], '456 Oak Ave')

    def test_update_address(self):
        self.client.force_authenticate(user=self.client_user)
        updated_data = {'street_address': '789 Pine Ln', 'city': 'New City'}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.address.refresh_from_db()
        self.assertEqual(self.address.street_address, '789 Pine Ln')

    def test_update_address_unauthenticated(self):
        updated_data = {'street_address': '789 Pine Ln', 'city': 'New City'}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_other_address_by_client(self):
        self.client.force_authenticate(user=self.client_user)
        updated_data = {'street_address': 'New Street', 'city': 'New City'}
        response = self.client.patch(self.other_detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Client cannot update other's address

    def test_update_address_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        updated_data = {'street_address': 'Admin Updated St', 'city': 'Admin City'}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.address.refresh_from_db()
        self.assertEqual(self.address.street_address, 'Admin Updated St')

    def test_delete_address(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Address.objects.count(), 1) # 2 initially, 1 deleted, 1 remaining (other_address)

    def test_delete_address_unauthenticated(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_other_address_by_client(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.delete(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Client cannot delete other's address

    def test_delete_address_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
