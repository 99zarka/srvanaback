from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import NotificationPreference, User
from api.models.users import UserType

class NotificationPreferenceTests(APITestCase):
    def setUp(self):
        self.usertype_customer = UserType.objects.create(user_type_name='Customer')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            user_type=self.usertype_customer
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='password123',
            user_type=self.usertype_customer
        )
        self.notification_preference_data = {
            'user': self.user2.user_id,
            'email_notifications': True,
            'sms_notifications': False,
            'push_notifications': True,
            'promotional_notifications': True
        }
        self.notification_preference = NotificationPreference.objects.create(
            user=self.user,
            email_notifications=False,
            sms_notifications=True,
            push_notifications=False,
            promotional_notifications=False
        )
        self.list_url = reverse('notificationpreference-list')
        self.detail_url = reverse('notificationpreference-detail', args=[self.notification_preference.id])

    def test_create_notification_preference(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(self.list_url, self.notification_preference_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NotificationPreference.objects.count(), 2)
        self.assertEqual(response.data['email_notifications'], True)

    def test_list_notification_preferences(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only preferences belonging to the authenticated user

    def test_retrieve_notification_preference(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['sms_notifications'], True)

    def test_update_notification_preference(self):
        self.client.force_authenticate(user=self.user)
        updated_data = {'sms_notifications': False, 'push_notifications': True}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification_preference.refresh_from_db()
        self.assertEqual(self.notification_preference.sms_notifications, False)

    def test_delete_notification_preference(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(NotificationPreference.objects.count(), 0)
