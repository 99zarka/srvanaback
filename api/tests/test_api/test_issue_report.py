from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import IssueReport, User, Order, Service, ServiceCategory
from api.models.users import UserType
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

class IssueReportTests(APITestCase):
    def setUp(self):
        self.client_usertype, created = UserType.objects.get_or_create(user_type_id=1, user_type_name="client")
        self.technician_usertype, created = UserType.objects.get_or_create(user_type_id=2, user_type_name="technician")
        self.admin_usertype, created = UserType.objects.get_or_create(user_type_id=3, user_type_name="admin")

        self.client_user = User.objects.create_user(
            username='clientuser',
            email='client@example.com',
            password='password123',
            user_type=self.client_usertype
        )
        self.technician_user = User.objects.create_user(
            username='techuser',
            email='technician@example.com',
            password='password123',
            user_type=self.technician_usertype
        )
        self.other_client_user = User.objects.create_user(
            username='otherclient',
            email='otherclient@example.com',
            password='password123',
            user_type=self.client_usertype
        )
        self.admin_user = User.objects.create(
            email="admin@example.com",
            username="adminuser",
            password=make_password("adminpassword123"),
            first_name="Admin",
            last_name="User",
            phone_number="0987654321",
            address="456 Admin Ave",
            user_type=self.admin_usertype,
            is_staff=True,
            is_superuser=True
        )

        self.service_category = ServiceCategory.objects.create(category_name='Electronics Repair')
        self.service = Service.objects.create(
            category=self.service_category,
            service_name='Test Service',
            description='Description for test service',
            service_type='Repair',
            base_inspection_fee=50.00
        )
        self.order1 = Order.objects.create(
            client_user=self.client_user,
            service=self.service,
            order_type='Repair',
            problem_description='Fix something for client 1',
            requested_location='Someplace 1',
            scheduled_date='2025-01-01',
            scheduled_time_start='09:00',
            scheduled_time_end='10:00',
            order_status='completed',
            creation_timestamp='2025-01-01'
        )
        self.order2 = Order.objects.create(
            client_user=self.other_client_user,
            service=self.service,
            order_type='Repair',
            problem_description='Fix something for client 2',
            requested_location='Someplace 2',
            scheduled_date='2025-01-02',
            scheduled_time_start='11:00',
            scheduled_time_end='12:00',
            order_status='pending',
            creation_timestamp='2025-01-02'
        )

        self.issue_report1 = IssueReport.objects.create(
            reporter=self.client_user,
            order=self.order1,
            title='Client 1 Issue',
            description='Issue for client 1',
            status='open'
        )
        self.issue_report2 = IssueReport.objects.create(
            reporter=self.other_client_user,
            order=self.order2,
            title='Client 2 Issue',
            description='Issue for client 2',
            status='closed'
        )

        self.issue_report_data = {
            'reporter': self.client_user.user_id,
            'order': self.order1.order_id,
            'title': 'New Issue Title',
            'description': 'Something is broken.',
            'status': 'open'
        }

        self.list_url = reverse('issuereport-list')
        self.detail_url1 = reverse('issuereport-detail', args=[self.issue_report1.id])
        self.detail_url2 = reverse('issuereport-detail', args=[self.issue_report2.id])

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    def test_create_issue_report_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, self.issue_report_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_issue_report_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.post(self.list_url, self.issue_report_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(IssueReport.objects.count(), 3)

    def test_create_issue_report_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.list_url, self.issue_report_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(IssueReport.objects.count(), 3)

    def test_list_issue_reports_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_issue_reports_client(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only reports belonging to the authenticated user

    def test_list_issue_reports_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Admin sees all reports

    def test_retrieve_issue_report_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_issue_report_client_owner(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Client 1 Issue')

    def test_retrieve_issue_report_client_not_owner(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url2) # client_user is not owner of issue_report2
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_issue_report_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Client 1 Issue')

    def test_update_issue_report_unauthenticated(self):
        self.client.force_authenticate(user=None)
        updated_data = {'status': 'in_progress'}
        response = self.client.patch(self.detail_url1, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_issue_report_client_owner(self):
        client = self.get_auth_client(self.client_user)
        updated_data = {'status': 'in_progress', 'description': 'Working on it.'}
        response = client.patch(self.detail_url1, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.issue_report1.refresh_from_db()
        self.assertEqual(self.issue_report1.status, 'in_progress')

    def test_update_issue_report_client_not_owner(self):
        client = self.get_auth_client(self.client_user)
        updated_data = {'status': 'in_progress'}
        response = client.patch(self.detail_url2, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_issue_report_admin(self):
        client = self.get_auth_client(self.admin_user)
        updated_data = {'status': 'resolved'}
        response = client.patch(self.detail_url1, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.issue_report1.refresh_from_db()
        self.assertEqual(self.issue_report1.status, 'resolved')

    def test_delete_issue_report_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.delete(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_issue_report_client_owner(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(IssueReport.objects.filter(id=self.issue_report1.id).exists(), False)

    def test_delete_issue_report_client_not_owner(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url2)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_issue_report_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.delete(self.detail_url1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(IssueReport.objects.filter(id=self.issue_report1.id).exists(), False)
