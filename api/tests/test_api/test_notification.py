from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import Notification, User
from api.models.users import UserType

class NotificationTests(APITestCase):
    def setUp(self):
        self.usertype_customer = UserType.objects.create(user_type_name='Customer')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            user_type=self.usertype_customer
        )
        self.notification_data = {
            'user': self.user.user_id,
            'title': 'Test Notification Title',
            'message': 'Test notification message',
            'is_read': False
        }
        self.notification = Notification.objects.create(
            user=self.user,
            title='Existing Notification Title',
            message='Existing notification',
            is_read=True
        )
        self.list_url = reverse('notification-list')
        self.detail_url = reverse('notification-detail', args=[self.notification.id])

    def test_create_notification(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_url, self.notification_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(response.data['message'], 'Test notification message')

    def test_list_notifications(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only notifications belonging to the authenticated user

    def test_retrieve_notification(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Existing notification')

    def test_update_notification(self):
        self.client.force_authenticate(user=self.user)
        updated_data = {'is_read': False}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.is_read, False)

    def test_delete_notification(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Notification.objects.count(), 0)
