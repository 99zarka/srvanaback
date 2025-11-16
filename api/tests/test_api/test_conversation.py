from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import Conversation, User
from api.models.users import UserType
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

class ConversationTests(APITestCase):
    def setUp(self):
        self.client_usertype, created = UserType.objects.get_or_create(user_type_id=1, user_type_name="client")
        self.technician_usertype, created = UserType.objects.get_or_create(user_type_id=2, user_type_name="technician")
        self.admin_usertype, created = UserType.objects.get_or_create(user_type_id=3, user_type_name="admin")

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
        self.other_client_user = User.objects.create_user(
            username='otherclient',
            email='otherclient@example.com',
            password='password123',
            user_type_name=self.client_usertype.user_type_name
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

        self.conversation1 = Conversation.objects.create()
        self.conversation1.participants.add(self.client_user, self.technician_user)

        self.conversation2 = Conversation.objects.create()
        self.conversation2.participants.add(self.client_user, self.other_client_user)

        self.conversation_data = {
            'participants': [self.client_user.user_id, self.technician_user.user_id],
        }

        self.list_url = reverse('conversation-list')
        self.detail_url1 = reverse('conversation-detail', args=[self.conversation1.id])
        self.detail_url2 = reverse('conversation-detail', args=[self.conversation2.id])

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    def test_create_conversation_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, self.conversation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_conversation_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.post(self.list_url, self.conversation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Conversation.objects.count(), 3) # 2 existing + 1 new

    def test_create_conversation_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.list_url, self.conversation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Conversation.objects.count(), 3)

    def test_list_conversations_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_conversations_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # client_user is in conversation1 and conversation2

    def test_list_conversations_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Admin sees all conversations

    def test_retrieve_conversation_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_conversation_client_owner(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.conversation1.id)

    def test_retrieve_conversation_client_not_owner(self):
        client = self.get_auth_client(self.other_client_user)
        response = client.get(self.detail_url1) # other_client_user is not in conversation1
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_conversation_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.conversation1.id)

    def test_update_conversation_unauthenticated(self):
        self.client.force_authenticate(user=None)
        updated_data = {'participants': [self.client_user.user_id]}
        response = self.client.patch(self.detail_url1, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_conversation_client_owner(self):
        client = self.get_auth_client(self.client_user)
        updated_data = {'participants': [self.client_user.user_id, self.admin_user.user_id]}
        response = client.patch(self.detail_url1, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.conversation1.refresh_from_db()
        self.assertIn(self.admin_user, self.conversation1.participants.all())

    def test_update_conversation_client_not_owner(self):
        client = self.get_auth_client(self.other_client_user)
        updated_data = {'participants': [self.other_client_user.user_id, self.admin_user.user_id]}
        response = client.patch(self.detail_url1, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_conversation_admin(self):
        client = self.get_auth_client(self.admin_user)
        updated_data = {'participants': [self.client_user.user_id, self.admin_user.user_id]}
        response = client.patch(self.detail_url1, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.conversation1.refresh_from_db()
        self.assertIn(self.admin_user, self.conversation1.participants.all())

    def test_delete_conversation_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.delete(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_conversation_client_owner(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Conversation.objects.filter(id=self.conversation1.id).exists(), False)

    def test_delete_conversation_client_not_owner(self):
        client = self.get_auth_client(self.other_client_user)
        response = client.delete(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_conversation_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.delete(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Conversation.objects.filter(id=self.conversation1.id).exists(), False)
