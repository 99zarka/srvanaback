from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from users.models import User, UserType
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

class UserTypeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client_usertype = UserType.objects.create(user_type_name='client')
        self.technician_usertype = UserType.objects.create(user_type_name='technician')
        self.admin_usertype = UserType.objects.create(user_type_name='admin')

        self.client_user = User.objects.create_user(
            username='clientuser',
            email='client@example.com',
            password='password123',
            user_type_name=self.client_usertype.user_type_name
        )
        self.technician_user = User.objects.create_user(
            username='techuser',
            email='technician@example.com',
            password='password123',
            user_type_name=self.technician_usertype.user_type_name
        )
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            username="adminuser",
            password="adminpassword123",
            user_type_name=self.admin_usertype.user_type_name,
        )

        self.usertype_data = {"user_type_name": "TestUserType"}
        self.updated_usertype_data = {"user_type_name": "UpdatedTestUserType"}

        self.list_url = reverse('usertype-list')
        self.detail_url = reverse('usertype-detail', args=[self.client_usertype.user_type_id])

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    def test_create_usertype_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, self.usertype_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_usertype_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.post(self.list_url, self.usertype_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_usertype_technician_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.post(self.list_url, self.usertype_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_usertype_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.list_url, self.usertype_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserType.objects.count(), 4)

    def test_list_usertypes(self):
        # No authentication needed for list view as it's public
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_retrieve_usertype(self):
        # No authentication needed for retrieve view as it's public
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_type_name'], 'client')

    def test_update_usertype_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.put(self.detail_url, self.updated_usertype_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_usertype_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.put(self.detail_url, self.updated_usertype_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_usertype_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.put(self.detail_url, self.updated_usertype_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client_usertype.refresh_from_db()
        self.assertEqual(self.client_usertype.user_type_name, 'UpdatedTestUserType')

    def test_delete_usertype_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_usertype_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_usertype_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserType.objects.filter(pk=self.client_usertype.pk).exists())
