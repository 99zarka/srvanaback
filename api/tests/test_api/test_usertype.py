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

class UserTypeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usertype, created = UserType.objects.get_or_create(user_type_id=1, user_type_name="Customer")
        self.register_url = '/api/register/'

        # Register a user and get tokens
        self.user_data = {
            "email": "usertypeuser@example.com",
            "username": "usertypeuser",
            "password": "usertypepassword123",
            "password2": "usertypepassword123",
            "first_name": "UserType",
            "last_name": "User",
            "phone_number": "7777777777",
            "address": "7 UserType St",
            # user_type is now optional and defaults to 1 in the model
        }
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.access_token = response.data['tokens']['access']

        # Authenticate the client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

        self.usertype_data = {"user_type_name": "TestUserType"}
        self.updated_usertype_data = {"user_type_name": "UpdatedTestUserType"}

    def test_create_usertype(self):
        response = self.client.post('/api/usertypes/', self.usertype_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserType.objects.count(), 2) # Expect 2: one from setUp, one created in this test
        self.assertEqual(UserType.objects.get(user_type_name='TestUserType').user_type_name, 'TestUserType')

    def test_get_all_usertypes(self):
        UserType.objects.get_or_create(user_type_name="AnotherUserType") # Use get_or_create
        response = self.client.get('/api/usertypes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # One from setUp, one created here

    def test_get_single_usertype(self):
        usertype, created = UserType.objects.get_or_create(user_type_name="SingleUserType") # Use get_or_create
        response = self.client.get(f'/api/usertypes/{usertype.user_type_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_type_name'], 'SingleUserType')

    def test_update_usertype(self):
        usertype, created = UserType.objects.get_or_create(user_type_name="OriginalUserType") # Use get_or_create
        response = self.client.put(f'/api/usertypes/{usertype.user_type_id}/', self.updated_usertype_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usertype.refresh_from_db()
        self.assertEqual(usertype.user_type_name, 'UpdatedTestUserType')

    def test_delete_usertype(self):
        usertype, created = UserType.objects.get_or_create(user_type_name="UserTypeToDelete") # Use get_or_create
        response = self.client.delete(f'/api/usertypes/{usertype.user_type_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # The count will be 1 if "Customer" from setUp still exists, or 0 if it's cleaned up.
        # For now, let's assert that the specific usertype is deleted.
        self.assertFalse(UserType.objects.filter(user_type_name="UserTypeToDelete").exists())
