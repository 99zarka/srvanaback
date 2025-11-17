from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from ..models import Message, Conversation
from users.models import User, UserType
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

class MessageTests(APITestCase):
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
        self.conversation2.participants.add(self.other_client_user, self.technician_user)

        self.message1 = Message.objects.create(
            conversation=self.conversation1,
            sender=self.client_user,
            content='Hello, technician!'
        )
        self.message2 = Message.objects.create(
            conversation=self.conversation1,
            sender=self.technician_user,
            content='Hello, client!'
        )
        self.message3 = Message.objects.create(
            conversation=self.conversation2,
            sender=self.other_client_user,
            content='Message in another conversation.'
        )

        self.message_data = {
            'conversation': self.conversation1.id,
            'sender': self.client_user.user_id,
            'content': 'New message from client.'
        }

        self.list_url = reverse('message-list')
        self.detail_url1 = reverse('message-detail', args=[self.message1.id])
        self.detail_url2 = reverse('message-detail', args=[self.message2.id])
        self.detail_url3 = reverse('message-detail', args=[self.message3.id])

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    def test_create_message_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, self.message_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_message_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.post(self.list_url, self.message_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 4)
        self.assertEqual(response.data['content'], 'New message from client.')

    def test_create_message_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.list_url, self.message_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 4)

    def test_list_messages_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_messages_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Only messages in conversations the client is part of

    def test_list_messages_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3) # Admin sees all messages

    def test_retrieve_message_client_participant(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Hello, technician!')

    def test_retrieve_message_client_not_participant(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url3) # client_user is not part of conversation2
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_message_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Hello, technician!')

    def test_update_message_unauthenticated(self):
        self.client.force_authenticate(user=None)
        updated_data = {'content': 'Updated content.'}
        response = self.client.patch(self.detail_url1, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_message_sender(self):
        client = self.get_auth_client(self.client_user)
        updated_data = {'content': 'Updated content by sender.'}
        response = client.patch(self.detail_url1, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.message1.refresh_from_db()
        self.assertEqual(self.message1.content, 'Updated content by sender.')

    def test_update_message_not_sender_but_participant(self):
        client = self.get_auth_client(self.client_user)
        updated_data = {'content': 'Updated content by participant.'}
        response = client.patch(self.detail_url2, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_message_admin(self):
        client = self.get_auth_client(self.admin_user)
        updated_data = {'content': 'Updated content by admin.'}
        response = client.patch(self.detail_url1, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.message1.refresh_from_db()
        self.assertEqual(self.message1.content, 'Updated content by admin.')

    def test_delete_message_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.delete(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_message_sender(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Message.objects.filter(id=self.message1.id).exists(), False)

    def test_delete_message_not_sender_but_participant(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url2)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_message_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.delete(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Message.objects.filter(id=self.message1.id).exists(), False)
