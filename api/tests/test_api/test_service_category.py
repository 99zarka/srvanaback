from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, datetime
from django.utils import timezone
from api.models import (
    UserType, User, ServiceCategory, Service, Order,
    TechnicianSkill, TechnicianAvailability, VerificationDocument
)
from rest_framework_simplejwt.tokens import RefreshToken

class ServiceCategoryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usertype, created = UserType.objects.get_or_create(user_type_id=1, user_type_name="Customer")
        self.register_url = '/api/register/'

        # Register a user and get tokens
        self.user_data = {
            "email": "servicecatuser@example.com",
            "username": "servicecatuser",
            "password": "servicecatpassword123",
            "password2": "servicecatpassword123",
            "first_name": "ServiceCat",
            "last_name": "User",
            "phone_number": "1111111111",
            "address": "1 ServiceCat St",
            # user_type is now optional and defaults to 1 in the model
        }
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.access_token = response.data['tokens']['access']

        # Authenticate the client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

        self.category_data = {
            "category_name": "TestCategory",
            "description": "Description for TestCategory",
            "icon_url": "http://example.com/icon.png"
        }
        self.updated_category_data = {
            "category_name": "UpdatedTestCategory",
            "description": "Updated description for TestCategory",
            "icon_url": "http://example.com/updated_icon.png"
        }

    def test_create_servicecategory_authenticated(self):
        response = self.client.post('/api/servicecategories/', self.category_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ServiceCategory.objects.count(), 1)
        self.assertEqual(ServiceCategory.objects.get().category_name, 'TestCategory')

    def test_create_servicecategory_unauthenticated(self):
        self.client.credentials() # Clear credentials
        response = self.client.post('/api/servicecategories/', self.category_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_servicecategories_authenticated(self):
        ServiceCategory.objects.create(category_name="AnotherCategory", description="Desc")
        response = self.client.get('/api/servicecategories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_single_servicecategory_authenticated(self):
        category = ServiceCategory.objects.create(category_name="SingleCategory", description="Desc")
        response = self.client.get(f'/api/servicecategories/{category.category_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['category_name'], 'SingleCategory')

    def test_update_servicecategory_authenticated(self):
        category = ServiceCategory.objects.create(category_name="OriginalCategory", description="Desc")
        response = self.client.put(f'/api/servicecategories/{category.category_id}/', self.updated_category_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        category.refresh_from_db()
        self.assertEqual(category.category_name, 'UpdatedTestCategory')

    def test_delete_servicecategory_authenticated(self):
        category = ServiceCategory.objects.create(category_name="CategoryToDelete", description="Desc")
        response = self.client.delete(f'/api/servicecategories/{category.category_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ServiceCategory.objects.count(), 0)
