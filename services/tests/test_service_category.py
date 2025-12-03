from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, datetime
from django.utils import timezone
from users.models import UserType, User
from services.models import ServiceCategory, Service
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse

class ServiceCategoryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create UserTypes
        self.client_usertype, created = UserType.objects.get_or_create(user_type_name="client")
        self.technician_usertype, created = UserType.objects.get_or_create(user_type_name="technician")
        self.admin_usertype, created = UserType.objects.get_or_create(user_type_name="admin")

        # Create Users
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
            first_name="Admin",
            last_name="User",
            phone_number="0987654321",
            address="456 Admin Ave",
            user_type_name=self.admin_usertype.user_type_name,
        )

        self.category = ServiceCategory.objects.create(category_name="TestCategory", description="Description for TestCategory", icon_url="http://example.com/icon.png")
        self.other_category = ServiceCategory.objects.create(category_name="OtherCategory", description="Description for OtherCategory", icon_url="http://example.com/other_icon.png")

        self.category_data = {
            "category_name": "NewCategory",
            "description": "Description for NewCategory",
            # # "icon_url": "http://example.com/new_icon.pn # Removed for testing ImageFieldg" # Removed for testing ImageField
        }
        self.updated_category_data = {
            "category_name": "UpdatedTestCategory",
            "description": "Updated description for TestCategory",
            # "icon_url": "http://example.com/updated_icon.png" # Removed for testing ImageField
        }

        self.list_url = reverse('servicecategory-list')
        self.detail_url = reverse('servicecategory-detail', args=[self.category.category_id])
        self.other_detail_url = reverse('servicecategory-detail', args=[self.other_category.category_id])

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    # --- Unauthenticated User Tests ---
    def test_unauthenticated_create_servicecategory(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, self.category_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_list_servicecategories(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Publicly accessible
        self.assertEqual(len(response.data['results']), 2)

    def test_unauthenticated_retrieve_servicecategory(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Publicly accessible
        self.assertEqual(response.data['category_name'], 'TestCategory')

    def test_unauthenticated_update_servicecategory(self):
        updated_data = {'category_name': 'Unauthorized Update'}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_delete_servicecategory(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Client User Tests ---
    def test_client_create_servicecategory_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.post(self.list_url, self.category_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_list_servicecategories(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_client_retrieve_servicecategory(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['category_name'], 'TestCategory')

    def test_client_update_servicecategory_forbidden(self):
        client = self.get_auth_client(self.client_user)
        updated_data = {'category_name': 'Client Update'}
        response = client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_delete_servicecategory_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Technician User Tests ---
    def test_technician_create_servicecategory_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.post(self.list_url, self.category_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_technician_list_servicecategories(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_technician_retrieve_servicecategory(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['category_name'], 'TestCategory')

    def test_technician_update_servicecategory_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        updated_data = {'category_name': 'Technician Update'}
        response = client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_technician_delete_servicecategory_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Admin User Tests ---
    def test_admin_create_servicecategory(self):
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.list_url, self.category_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ServiceCategory.objects.count(), 3)
        self.assertEqual(response.data['category_name'], 'NewCategory')

    def test_admin_list_servicecategories(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_admin_retrieve_servicecategory(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['category_name'], 'TestCategory')

    def test_admin_update_servicecategory(self):
        client = self.get_auth_client(self.admin_user)
        response = client.patch(self.detail_url, self.updated_category_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.category_name, 'UpdatedTestCategory')

    def test_admin_delete_servicecategory(self):
        client = self.get_auth_client(self.admin_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ServiceCategory.objects.count(), 1) # One deleted
