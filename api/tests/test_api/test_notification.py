from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import Notification, User
from api.models.users import UserType

class NotificationTests(APITestCase):
    def setUp(self):
        self.usertype_client = UserType.objects.create(user_type_name='client')
        self.usertype_admin = UserType.objects.create(user_type_name='admin')

        self.client_user = User.objects.create_user(
            username='clientuser',
            email='client@example.com',
            password='password123',
            user_type=self.usertype_client
        )
        self.other_client_user = User.objects.create_user(
            username='otherclient',
            email='other@example.com',
            password='password123',
            user_type=self.usertype_client
        )
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='password123',
            user_type=self.usertype_admin
        )

        self.notification_data = {
            'title': 'Test Notification Title',
            'message': 'Test notification message',
            'is_read': False
        }
        self.notification = Notification.objects.create(
            user=self.client_user,
            title='Existing Notification Title',
            message='Existing notification',
            is_read=True
        )
        self.other_notification = Notification.objects.create(
            user=self.other_client_user,
            title='Other Notification Title',
            message='Other notification message',
            is_read=False
        )

        self.list_url = reverse('notification-list')
        self.detail_url = reverse('notification-detail', args=[self.notification.id])
        self.other_detail_url = reverse('notification-detail', args=[self.other_notification.id])

    # --- Unauthenticated User Tests ---
    def test_unauthenticated_create_notification(self):
        response = self.client.post(self.list_url, self.notification_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_list_notifications(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_retrieve_notification(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_update_notification(self):
        updated_data = {'is_read': False}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_delete_notification(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Client User Tests (Owner) ---
    def test_client_create_notification(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(self.list_url, self.notification_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.filter(user=self.client_user).count(), 2)
        self.assertEqual(response.data['message'], 'Test notification message')

    def test_client_list_notifications(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only notifications belonging to the authenticated user
        self.assertEqual(response.data[0]['message'], 'Existing notification')

    def test_client_retrieve_notification(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Existing notification')

    def test_client_update_notification(self):
        self.client.force_authenticate(user=self.client_user)
        updated_data = {'is_read': False}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.is_read, False)

    def test_client_delete_notification(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Notification.objects.filter(user=self.client_user).count(), 0)

    # --- Client User Tests (Non-Owner) ---
    def test_client_create_notification_for_other_user(self):
        self.client.force_authenticate(user=self.client_user)
        other_user_notification_data = {
            'title': 'Other User Notification',
            'message': 'Message for other user',
            'is_read': False
        }
        response = self.client.post(self.list_url, other_user_notification_data, format='json')
        # Should be able to create, and the notification will be associated with the authenticated user due to serializer logic
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.filter(user=self.client_user).count(), 2)
        self.assertEqual(Notification.objects.filter(user=self.other_client_user).count(), 1)


    def test_client_retrieve_other_notification(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Should not find other user's notification

    def test_client_update_other_notification(self):
        self.client.force_authenticate(user=self.client_user)
        updated_data = {'is_read': True}
        response = self.client.patch(self.other_detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_client_delete_other_notification(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.delete(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Admin User Tests ---
    def test_admin_create_notification(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.list_url, self.notification_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 3) # Original 2 + 1 new
        self.assertEqual(response.data['message'], 'Test notification message')

    def test_admin_list_notifications(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # All notifications
        self.assertEqual(response.data[0]['message'], 'Existing notification')
        self.assertEqual(response.data[1]['message'], 'Other notification message')

    def test_admin_retrieve_notification(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Existing notification')

    def test_admin_update_notification(self):
        self.client.force_authenticate(user=self.admin_user)
        updated_data = {'is_read': False}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.is_read, False)

    def test_admin_delete_notification(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Notification.objects.count(), 1) # One deleted
