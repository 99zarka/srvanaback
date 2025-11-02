from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import ProjectOffer, User, Order, Service, ServiceCategory
from api.models.users import UserType

class ProjectOfferTests(APITestCase):
    def setUp(self):
        self.usertype_customer = UserType.objects.create(user_type_name='Customer')
        self.usertype_technician = UserType.objects.create(user_type_name='Technician')

        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='password123',
            user_type=self.usertype_customer
        )
        self.technician = User.objects.create_user(
            username='technician',
            email='technician@example.com',
            password='password123',
            user_type=self.usertype_technician
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
            client_user=self.customer,
            service=self.service,
            order_type='Repair',
            problem_description='Fix something',
            requested_location='Someplace',
            scheduled_date='2025-01-01',
            scheduled_time_start='09:00',
            scheduled_time_end='10:00',
            order_status='pending',
            creation_timestamp='2025-01-01'
        )
        self.project_offer_data = {
            'order': self.order.order_id,
            'technician_user': self.technician.user_id,
            'offered_price': 150.00,
            'offer_description': 'Offer description',
            'status': 'pending',
            'offer_date': '2025-01-01'
        }
        self.project_offer = ProjectOffer.objects.create(
            order=self.order,
            technician_user=self.technician,
            offered_price=120.00,
            offer_description='Existing offer',
            status='accepted',
            offer_date='2025-01-01'
        )
        self.list_url = reverse('projectoffer-list')
        self.detail_url = reverse('projectoffer-detail', args=[self.project_offer.offer_id])

    def test_create_project_offer(self):
        self.client.force_authenticate(user=self.technician)
        response = self.client.post(self.list_url, self.project_offer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProjectOffer.objects.count(), 2)
        self.assertEqual(response.data['offered_price'], '150.00')

    def test_list_project_offers(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only the existing offer should be visible to customer

    def test_retrieve_project_offer(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['offered_price'], '120.00')

    def test_update_project_offer(self):
        self.client.force_authenticate(user=self.technician)
        updated_data = {'offer_description': 'Updated offer description', 'offered_price': 160.00}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project_offer.refresh_from_db()
        self.assertEqual(self.project_offer.offered_price, 160.00)

    def test_delete_project_offer(self):
        self.client.force_authenticate(user=self.technician)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ProjectOffer.objects.count(), 0)
