from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import Conversation, User
from api.models.users import UserType

class ConversationTests(APITestCase):
    def setUp(self):
        self.usertype_customer = UserType.objects.create(user_type_name='Customer')
        self.usertype_technician = UserType.objects.create(user_type_name='Technician')

        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password123',
            user_type=self.usertype_customer
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='password123',
            user_type=self.usertype_technician
        )
        self.conversation_data = {
            'participants': [self.user1.user_id, self.user2.user_id],
        }
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)

        self.list_url = reverse('conversation-list')
        self.detail_url = reverse('conversation-detail', args=[self.conversation.id])

    def test_create_conversation(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.list_url, self.conversation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Conversation.objects.count(), 2)

    def test_list_conversations(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only conversations involving the authenticated user

    def test_retrieve_conversation(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_conversation(self):
        self.client.force_authenticate(user=self.user1)
        # No subject field to update
        updated_data = {}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # No assertion for subject as it doesn't exist

    def test_delete_conversation(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Conversation.objects.count(), 0)
