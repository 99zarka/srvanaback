from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import IssueReport, User, Order, Service, ServiceCategory
from api.models.users import UserType

class IssueReportTests(APITestCase):
    def setUp(self):
        self.usertype_customer = UserType.objects.create(user_type_name='Customer')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            user_type=self.usertype_customer
        )
        self.service_category = ServiceCategory.objects.create(category_name='Electronics Repair')
        self.service = Service.objects.create(
            category=self.service_category,
            service_name='Test Service',
            description='Description for test service',
            service_type='Repair',
            base_inspection_fee=50.00
        )
        self.order = Order.objects.create(
            client_user=self.user,
            service=self.service,
            order_type='Repair',
            problem_description='Fix something',
            requested_location='Someplace',
            scheduled_date='2025-01-01',
            scheduled_time_start='09:00',
            scheduled_time_end='10:00',
            order_status='completed',
            creation_timestamp='2025-01-01'
        )
        self.issue_report_data = {
            'reporter': self.user.user_id,
            'order': self.order.order_id,
            'title': 'New Issue Title',
            'description': 'Something is broken.',
            'status': 'open'
        }
        self.issue_report = IssueReport.objects.create(
            reporter=self.user,
            order=self.order,
            title='Existing Issue',
            description='I want a new feature.',
            status='closed'
        )
        self.list_url = reverse('issuereport-list')
        self.detail_url = reverse('issuereport-detail', args=[self.issue_report.id])

    def test_create_issue_report(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_url, self.issue_report_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(IssueReport.objects.count(), 2)
        self.assertEqual(response.data['title'], 'New Issue Title')

    def test_list_issue_reports(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only reports belonging to the authenticated user

    def test_retrieve_issue_report(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Existing Issue')

    def test_update_issue_report(self):
        self.client.force_authenticate(user=self.user)
        updated_data = {'status': 'in_progress', 'description': 'Working on it.'}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.issue_report.refresh_from_db()
        self.assertEqual(self.issue_report.status, 'in_progress')

    def test_delete_issue_report(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(IssueReport.objects.count(), 0)
