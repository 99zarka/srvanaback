from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import Address, User
from api.models.users import UserType

class AddressTests(APITestCase):
    def setUp(self):
        self.usertype_customer = UserType.objects.create(user_type_name='Customer')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            user_type=self.usertype_customer
        )
        self.address_data = {
            'user': self.user.user_id,
            'street_address': '123 Main St',
            'city': 'Anytown',
            'state': 'CA',
            'zip_code': '90210',
            'country': 'USA'
        }
        self.address = Address.objects.create(
            user=self.user,
            street_address='456 Oak Ave',
            city='Otherville',
            state='NY',
            zip_code='10001',
            country='USA'
        )
        self.list_url = reverse('address-list')
        self.detail_url = reverse('address-detail', args=[self.address.id])

    def test_create_address(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_url, self.address_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Address.objects.count(), 2)
        self.assertEqual(response.data['street_address'], '123 Main St')

    def test_list_addresses(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only addresses belonging to the authenticated user

    def test_retrieve_address(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['street_address'], '456 Oak Ave')

    def test_update_address(self):
        self.client.force_authenticate(user=self.user)
        updated_data = {'street_address': '789 Pine Ln', 'city': 'New City'}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.address.refresh_from_db()
        self.assertEqual(self.address.street_address, '789 Pine Ln')

    def test_delete_address(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Address.objects.count(), 0)
