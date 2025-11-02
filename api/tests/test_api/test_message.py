from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import Message, Conversation, User
from api.models.users import UserType

class MessageTests(APITestCase):
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
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)

        self.message_data = {
            'conversation': self.conversation.id,
            'sender': self.user1.user_id,
            'content': 'Hello, how are you?'
        }
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user2,
            content='I am good, thanks!'
        )
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content='I sent this message.'
        )
        self.list_url = reverse('message-list')
        self.detail_url = reverse('message-detail', args=[self.message.id])

    def test_create_message(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.list_url, self.message_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 3)
        self.assertEqual(response.data['content'], 'Hello, how are you?')

    def test_list_messages(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # All messages in the conversation should be visible

    def test_retrieve_message(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'I am good, thanks!')

    def test_update_message(self):
        self.client.force_authenticate(user=self.user2)
        updated_data = {'content': 'I am doing great!'}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.message.refresh_from_db()
        self.assertEqual(self.message.content, 'I am doing great!')

    def test_delete_message(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Message.objects.count(), 1)
