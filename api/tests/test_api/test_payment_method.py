from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import PaymentMethod, User
from api.models.users import UserType

class PaymentMethodTests(APITestCase):
    def setUp(self):
        self.usertype_customer = UserType.objects.create(user_type_name='Customer')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            user_type=self.usertype_customer
        )
        self.payment_method_data = {
            'user': self.user.user_id,
            'card_type': 'Visa',
            'last_four_digits': '1111',
            'expiration_date': '12/25',
            'card_holder_name': 'Test User',
            'is_default': True
        }
        self.payment_method = PaymentMethod.objects.create(
            user=self.user,
            card_type='MasterCard',
            last_four_digits='2222',
            expiration_date='10/24',
            card_holder_name='Test User',
            is_default=False
        )
        self.list_url = reverse('paymentmethod-list')
        self.detail_url = reverse('paymentmethod-detail', args=[self.payment_method.id])

    def test_create_payment_method(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_url, self.payment_method_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PaymentMethod.objects.count(), 2)
        self.assertEqual(response.data['card_type'], 'Visa')

    def test_list_payment_methods(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only payment methods belonging to the authenticated user

    def test_retrieve_payment_method(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['card_type'], 'MasterCard')

    def test_update_payment_method(self):
        self.client.force_authenticate(user=self.user)
        updated_data = {'is_default': True, 'expiration_date': '11/26'}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment_method.refresh_from_db()
        self.assertEqual(self.payment_method.is_default, True)

    def test_delete_payment_method(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PaymentMethod.objects.count(), 0)
