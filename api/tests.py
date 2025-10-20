from django.test import TestCase
from .models import UserType, User, ServiceCategory, Service, Order
from datetime import date

class ModelTestCase(TestCase):
    def setUp(self):
        # Create a UserType
        self.user_type = UserType.objects.create(user_type_name="Client")

        # Create a User
        self.user = User.objects.create(
            user_type=self.user_type,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone_number="1234567890",
            password="securepassword",
            registration_date=date.today(),
            username="johndoe",
            account_status="Active"
        )

        # Create a ServiceCategory
        self.service_category = ServiceCategory.objects.create(
            category_name="Plumbing",
            description="Services related to plumbing."
        )

        # Create a Service
        self.service = Service.objects.create(
            category=self.service_category,
            service_name="Pipe Repair",
            description="Repairing leaky pipes.",
            service_type="Repair",
            base_inspection_fee=50.00
        )

        # Create an Order
        self.order = Order.objects.create(
            client_user=self.user,
            service=self.service,
            order_type="Emergency",
            problem_description="Burst pipe in kitchen.",
            requested_location="123 Main St",
            scheduled_date=date.today(),
            scheduled_time_start="09:00",
            scheduled_time_end="10:00",
            order_status="Pending",
            creation_timestamp=date.today()
        )

    def test_user_type_creation(self):
        user_type = UserType.objects.get(user_type_name="Client")
        self.assertEqual(user_type.user_type_name, "Client")

    def test_user_creation(self):
        user = User.objects.get(email="john.doe@example.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.user_type.user_type_name, "Client")

    def test_service_category_creation(self):
        service_category = ServiceCategory.objects.get(category_name="Plumbing")
        self.assertEqual(service_category.description, "Services related to plumbing.")

    def test_service_creation(self):
        service = Service.objects.get(service_name="Pipe Repair")
        self.assertEqual(service.service_type, "Repair")
        self.assertEqual(service.category.category_name, "Plumbing")

    def test_order_creation(self):
        order = Order.objects.get(order_type="Emergency")
        self.assertEqual(order.client_user.email, "john.doe@example.com")
        self.assertEqual(order.service.service_name, "Pipe Repair")
        self.assertEqual(order.order_status, "Pending")

    def test_order_relationships(self):
        order = Order.objects.get(order_id=self.order.order_id)
        self.assertEqual(order.client_user, self.user)
        self.assertEqual(order.service, self.service)
