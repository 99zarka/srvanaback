from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from api.models import Review, User, Service, ServiceCategory, Order
from api.models.users import UserType

class ReviewTests(APITestCase):
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
            problem_description='Broken screen',
            requested_location='Customer Home',
            scheduled_date='2025-01-01',
            scheduled_time_start='09:00',
            scheduled_time_end='10:00',
            order_status='pending',
            creation_timestamp='2025-01-01'
        )
        self.review_data = {
            'reviewer': self.customer.pk,
            'technician': self.technician.pk,
            'order': self.order.pk,
            'rating': 5,
            'comment': 'Excellent service!'
        }
        self.review = Review.objects.create(
            reviewer=self.customer,
            technician=self.technician,
            order=self.order,
            rating=4,
            comment='Good service.'
        )
        self.list_url = reverse('review-list')
        self.detail_url = reverse('review-detail', args=[self.review.id])

    def test_create_review(self):
        self.client.force_authenticate(user=self.customer)
        
        # Create a new service and order for this test to avoid OneToOneField conflict
        new_service = Service.objects.create(
            category=self.service_category,
            service_name='New Test Service',
            description='Description for new test service',
            service_type='Repair',
            base_inspection_fee=60.00
        )
        new_order = Order.objects.create(
            client_user=self.customer,
            service=new_service,
            order_type='Repair',
            problem_description='Another broken screen',
            requested_location='Customer New Home',
            scheduled_date='2025-01-02',
            scheduled_time_start='11:00',
            scheduled_time_end='12:00',
            order_status='pending',
            creation_timestamp='2025-01-02'
        )
        new_review_data = {
            'reviewer': self.customer.pk,
            'technician': self.technician.pk,
            'order': new_order.pk,
            'rating': 5,
            'comment': 'Excellent service again!'
        }

        response = self.client.post(self.list_url, new_review_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 2)
        self.assertEqual(response.data['rating'], 5)

    def test_list_reviews(self):
        self.client.force_authenticate(user=self.customer)
        
        # Create another review for listing test
        new_service = Service.objects.create(
            category=self.service_category,
            service_name='Another Test Service',
            description='Description for another test service',
            service_type='Repair',
            base_inspection_fee=70.00
        )
        new_order = Order.objects.create(
            client_user=self.customer,
            service=new_service,
            order_type='Repair',
            problem_description='Yet another broken screen',
            requested_location='Customer Third Home',
            scheduled_date='2025-01-03',
            scheduled_time_start='13:00',
            scheduled_time_end='14:00',
            order_status='pending',
            creation_timestamp='2025-01-03'
        )
        Review.objects.create(
            reviewer=self.customer,
            technician=self.technician,
            order=new_order,
            rating=5,
            comment='Fantastic service.'
        )

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # All reviews should be visible

    def test_retrieve_review(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 4)

    def test_update_review(self):
        self.client.force_authenticate(user=self.customer)
        updated_data = {'rating': 3, 'comment': 'Service was okay.'}
        response = self.client.patch(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 3)

    def test_delete_review(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Review.objects.count(), 0)
