from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from users.models import User, UserType
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

class UserAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client_usertype = UserType.objects.create(user_type_name='client')
        self.admin_usertype = UserType.objects.create(user_type_name='admin')

        self.client_user = User.objects.create_user(
            username='clientuser',
            email='client@example.com',
            password='password123',
            user_type_name=self.client_usertype.user_type_name
        )
        self.other_client_user = User.objects.create_user(
            username='otherclient',
            email='other@example.com',
            password='password123',
            user_type_name=self.client_usertype.user_type_name
        )
        self.admin_user = User.objects.create(
            email="admin@example.com",
            username="adminuser",
            password=make_password("adminpassword123"),
            user_type=self.admin_usertype,
            is_staff=True,
            is_superuser=True
        )

        self.list_url = reverse('user-list')
        self.detail_url = reverse('user-detail', args=[self.client_user.user_id])
        self.other_detail_url = reverse('user-detail', args=[self.other_client_user.user_id])

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    def test_list_users_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_users_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Should only see self

    def test_list_users_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3) # Admin sees all

    def test_retrieve_user_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_own_user_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.client_user.email)

    def test_retrieve_other_user_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_user_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.patch(self.detail_url, {'first_name': 'test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_own_user_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.patch(self.detail_url, {'first_name': 'Updated'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.first_name, 'Updated')

    def test_update_other_user_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.patch(self.other_detail_url, {'first_name': 'Updated'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.patch(self.detail_url, {'first_name': 'AdminUpdate'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.first_name, 'AdminUpdate')

    def test_delete_user_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_own_user_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.client_user.pk).exists())

    def test_delete_other_user_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_user_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.client_user.pk).exists())
