from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from ..models import NotificationPreference
from users.models import User, UserType

class NotificationPreferenceTests(APITestCase):
    def setUp(self):
        self.client_usertype = UserType.objects.create(user_type_name='client')
        self.technician_usertype = UserType.objects.create(user_type_name='technician')
        self.admin_usertype = UserType.objects.create(user_type_name='admin')

        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='password123',
            user_type_name=self.admin_usertype.user_type_name
        )
        self.client_user = User.objects.create_user(
            username='clientuser',
            email='client@example.com',
            password='password123',
            user_type_name=self.client_usertype.user_type_name
        )
        self.other_client_user = User.objects.create_user(
            username='otherclient',
            email='other@example.com',
            password='password123',
            user_type_name=self.client_usertype.user_type_name
        )
        self.technician_user = User.objects.create_user(
            username='techuser',
            email='tech@example.com',
            password='password123',
            user_type_name=self.technician_usertype.user_type_name
        )
        
        self.notification_preference_data = {
            'email_notifications': True,
            'sms_notifications': False,
            'push_notifications': True,
            'promotional_notifications': True
        }
        self.notification_preference = NotificationPreference.objects.create(
            user=self.client_user,
            email_notifications=False,
            sms_notifications=True,
            push_notifications=False,
            promotional_notifications=False
        )
        self.list_url = reverse('notificationpreference-list')
        self.detail_url = reverse('notificationpreference-detail', args=[self.notification_preference.id])
    def test_unauthenticated_access(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(self.list_url, self.notification_preference_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_create_notification_preference(self):
        self.client.force_authenticate(user=self.other_client_user)
        response = self.client.post(self.list_url, self.notification_preference_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NotificationPreference.objects.count(), 2)
        self.assertEqual(response.data['user'], self.other_client_user.user_id) # User should be automatically assigned

    def test_client_list_own_notification_preferences(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], self.client_user.user_id)

    def test_client_retrieve_own_notification_preference(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.client_user.user_id)

    def test_client_retrieve_other_notification_preference_forbidden(self):
        self.client.force_authenticate(user=self.other_client_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_update_own_notification_preference(self):
        self.client.force_authenticate(user=self.client_user)
        updated_data = {'sms_notifications': False, 'push_notifications': True}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification_preference.refresh_from_db()
        self.assertEqual(self.notification_preference.sms_notifications, False)

    def test_client_update_other_notification_preference_forbidden(self):
        self.client.force_authenticate(user=self.other_client_user)
        updated_data = {'sms_notifications': False}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_delete_own_notification_preference(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(NotificationPreference.objects.count(), 0)

    def test_client_delete_other_notification_preference_forbidden(self):
        self.client.force_authenticate(user=self.other_client_user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(NotificationPreference.objects.count(), 1) # Should not be deleted

    def test_admin_list_all_notification_preferences(self):
        NotificationPreference.objects.create(
            user=self.other_client_user,
            email_notifications=True,
            sms_notifications=True,
            push_notifications=True,
            promotional_notifications=True
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Admin should see all preferences

    def test_admin_retrieve_any_notification_preference(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.client_user.user_id)

    def test_admin_update_any_notification_preference(self):
        self.client.force_authenticate(user=self.admin_user)
        updated_data = {'sms_notifications': False, 'push_notifications': True}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification_preference.refresh_from_db()
        self.assertEqual(self.notification_preference.sms_notifications, False)

    def test_admin_delete_any_notification_preference(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(NotificationPreference.objects.count(), 0)

    def test_technician_access_forbidden(self):
        self.client.force_authenticate(user=self.technician_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.post(self.list_url, self.notification_preference_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.patch(self.detail_url, {'sms_notifications': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
