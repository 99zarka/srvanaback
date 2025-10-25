from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, datetime
from django.utils import timezone
from api.models import (
    UserType, User, ServiceCategory, Service, Order,
    TechnicianSkill, TechnicianAvailability, VerificationDocument
)

class UserTypeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usertype_data = {"user_type_name": "TestUserType"}
        self.updated_usertype_data = {"user_type_name": "UpdatedTestUserType"}

    def test_create_usertype(self):
        response = self.client.post('/api/usertypes/', self.usertype_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserType.objects.count(), 1)
        self.assertEqual(UserType.objects.get().user_type_name, 'TestUserType')

    def test_get_all_usertypes(self):
        UserType.objects.create(user_type_name="AnotherUserType")
        response = self.client.get('/api/usertypes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only one created in this test, not including setUp

    def test_get_single_usertype(self):
        usertype = UserType.objects.create(user_type_name="SingleUserType")
        response = self.client.get(f'/api/usertypes/{usertype.user_type_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_type_name'], 'SingleUserType')

    def test_update_usertype(self):
        usertype = UserType.objects.create(user_type_name="OriginalUserType")
        response = self.client.put(f'/api/usertypes/{usertype.user_type_id}/', self.updated_usertype_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usertype.refresh_from_db()
        self.assertEqual(usertype.user_type_name, 'UpdatedTestUserType')

    def test_delete_usertype(self):
        usertype = UserType.objects.create(user_type_name="UserTypeToDelete")
        response = self.client.delete(f'/api/usertypes/{usertype.user_type_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserType.objects.count(), 0)


class UserAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usertype = UserType.objects.create(user_type_name="Customer")
        self.user_data = {
            "user_type": self.usertype.user_type_id,
            "first_name": "Test",
            "last_name": "User",
            "email": "testuser@example.com",
            "password": "testpassword123",
            "registration_date": timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0)),
            "phone_number": "1234567890",
            "username": "testuser"
        }
        self.updated_user_data = {
            "user_type": self.usertype.user_type_id,
            "first_name": "Updated",
            "last_name": "User",
            "email": "updateduser@example.com",
            "phone_number": "0987654321",
            "username": "updateduser",
            "registration_date": timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0))
        }

    def test_create_user(self):
        response = self.client.post('/api/users/', self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'testuser@example.com')

    def test_get_all_users(self):
        User.objects.create(
            user_type=self.usertype,
            first_name="Another", last_name="User", email="another@example.com",
            password="password", registration_date=timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0)), phone_number="1112223333",
            username="anotheruser"
        )
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only one created in this test, not including setUp

    def test_get_single_user(self):
        user = User.objects.create(
            user_type=self.usertype,
            first_name="Single", last_name="User", email="single@example.com",
            password="password", registration_date=timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0)), phone_number="4445556666",
            username="singleuser"
        )
        response = self.client.get(f'/api/users/{user.user_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'single@example.com')

    def test_update_user(self):
        user = User.objects.create(
            user_type=self.usertype,
            first_name="Original", last_name="User", email="original@example.com",
            password="password", registration_date=timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0)), phone_number="7778889999",
            username="originaluser"
        )
        response = self.client.put(f'/api/users/{user.user_id}/', self.updated_user_data, format='json')
        if response.status_code != status.HTTP_200_OK:
            print(f"Update User Error: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.email, 'updateduser@example.com')

    def test_delete_user(self):
        user = User.objects.create(
            user_type=self.usertype,
            first_name="User", last_name="ToDelete", email="todelete@example.com",
            password="password", registration_date=timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0)), phone_number="0001112222",
            username="usertodelete"
        )
        response = self.client.delete(f'/api/users/{user.user_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 0)


class ServiceCategoryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category_data = {
            "category_name": "TestCategory",
            "description": "Description for TestCategory",
            "icon_url": "http://example.com/icon.png"
        }
        self.updated_category_data = {
            "category_name": "UpdatedTestCategory",
            "description": "Updated description for TestCategory",
            "icon_url": "http://example.com/updated_icon.png"
        }

    def test_create_servicecategory(self):
        response = self.client.post('/api/servicecategories/', self.category_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ServiceCategory.objects.count(), 1)
        self.assertEqual(ServiceCategory.objects.get().category_name, 'TestCategory')

    def test_get_all_servicecategories(self):
        ServiceCategory.objects.create(category_name="AnotherCategory", description="Desc")
        response = self.client.get('/api/servicecategories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_single_servicecategory(self):
        category = ServiceCategory.objects.create(category_name="SingleCategory", description="Desc")
        response = self.client.get(f'/api/servicecategories/{category.category_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['category_name'], 'SingleCategory')

    def test_update_servicecategory(self):
        category = ServiceCategory.objects.create(category_name="OriginalCategory", description="Desc")
        response = self.client.put(f'/api/servicecategories/{category.category_id}/', self.updated_category_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        category.refresh_from_db()
        self.assertEqual(category.category_name, 'UpdatedTestCategory')

    def test_delete_servicecategory(self):
        category = ServiceCategory.objects.create(category_name="CategoryToDelete", description="Desc")
        response = self.client.delete(f'/api/servicecategories/{category.category_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ServiceCategory.objects.count(), 0)


class ServiceAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = ServiceCategory.objects.create(category_name="TestCategoryForService", description="Temp category")
        self.service_data = {
            "category": self.category.category_id,
            "service_name": "TestService",
            "description": "Description for TestService",
            "service_type": "Repair",
            "base_inspection_fee": 50.00,
            "estimated_price_range_min": 100.00,
            "estimated_price_range_max": 500.00,
            "emergency_surcharge_percentage": 10.00
        }
        self.updated_service_data = {
            "category": self.category.category_id,
            "service_name": "UpdatedTestService",
            "description": "Updated description for TestService",
            "service_type": "Maintenance",
            "base_inspection_fee": 75.00,
            "estimated_price_range_min": 150.00,
            "estimated_price_range_max": 600.00,
            "emergency_surcharge_percentage": 15.00
        }

    def test_create_service(self):
        response = self.client.post('/api/services/', self.service_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Service.objects.count(), 1)
        self.assertEqual(Service.objects.get().service_name, 'TestService')

    def test_get_all_services(self):
        Service.objects.create(
            category=self.category, service_name="AnotherService", description="Desc",
            service_type="Installation", base_inspection_fee=30.00
        )
        response = self.client.get('/api/services/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_single_service(self):
        service = Service.objects.create(
            category=self.category, service_name="SingleService", description="Desc",
            service_type="Repair", base_inspection_fee=60.00
        )
        response = self.client.get(f'/api/services/{service.service_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['service_name'], 'SingleService')

    def test_update_service(self):
        service = Service.objects.create(
            category=self.category, service_name="OriginalService", description="Desc",
            service_type="Repair", base_inspection_fee=40.00
        )
        response = self.client.put(f'/api/services/{service.service_id}/', self.updated_service_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        service.refresh_from_db()
        self.assertEqual(service.service_name, 'UpdatedTestService')

    def test_delete_service(self):
        service = Service.objects.create(
            category=self.category, service_name="ServiceToDelete", description="Desc",
            service_type="Repair", base_inspection_fee=70.00
        )
        response = self.client.delete(f'/api/services/{service.service_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Service.objects.count(), 0)


class TechnicianAvailabilityAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usertype = UserType.objects.create(user_type_name="Technician")
        self.technician_user = User.objects.create(
            user_type=self.usertype,
            first_name="Tech", last_name="User", email="techuser@example.com",
            password="techpassword123", registration_date=timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0)), phone_number="1122334455",
            username="techuser"
        )
        self.availability_data = {
            "technician_user": self.technician_user.user_id,
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "17:00",
            "is_available": True
        }
        self.updated_availability_data = {
            "technician_user": self.technician_user.user_id,
            "day_of_week": "Tuesday",
            "start_time": "10:00",
            "end_time": "18:00",
            "is_available": False
        }

    def test_create_technicianavailability(self):
        response = self.client.post('/api/technicianavailabilities/', self.availability_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TechnicianAvailability.objects.count(), 1)
        self.assertEqual(TechnicianAvailability.objects.get().day_of_week, 'Monday')

    def test_get_all_technicianavailabilities(self):
        TechnicianAvailability.objects.create(
            technician_user=self.technician_user, day_of_week="Wednesday",
            start_time="08:00", end_time="16:00", is_available=True
        )
        response = self.client.get('/api/technicianavailabilities/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_single_technicianavailability(self):
        availability = TechnicianAvailability.objects.create(
            technician_user=self.technician_user, day_of_week="Thursday",
            start_time="11:00", end_time="19:00", is_available=True
        )
        response = self.client.get(f'/api/technicianavailabilities/{availability.availability_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['day_of_week'], 'Thursday')

    def test_update_technicianavailability(self):
        availability = TechnicianAvailability.objects.create(
            technician_user=self.technician_user, day_of_week="Friday",
            start_time="12:00", end_time="20:00", is_available=True
        )
        response = self.client.put(f'/api/technicianavailabilities/{availability.availability_id}/', self.updated_availability_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        availability.refresh_from_db()
        self.assertEqual(availability.day_of_week, 'Tuesday')

    def test_delete_technicianavailability(self):
        availability = TechnicianAvailability.objects.create(
            technician_user=self.technician_user, day_of_week="Saturday",
            start_time="09:00", end_time="17:00", is_available=True
        )
        response = self.client.delete(f'/api/technicianavailabilities/{availability.availability_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TechnicianAvailability.objects.count(), 0)


class TechnicianSkillAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usertype = UserType.objects.create(user_type_name="Technician")
        self.technician_user = User.objects.create(
            user_type=self.usertype,
            first_name="Skill", last_name="Tech", email="skilltech@example.com",
            password="skilltechpassword", registration_date=timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0)), phone_number="9988776655",
            username="skilltech"
        )
        self.category = ServiceCategory.objects.create(category_name="SkillTestCategory", description="Category for skill test")
        self.service = Service.objects.create(
            category=self.category, service_name="SkillTestService", description="Service for skill test",
            service_type="Installation", base_inspection_fee=30.00
        )
        self.skill_data = {
            "technician_user": self.technician_user.user_id,
            "service": self.service.service_id,
            "experience_level": "Expert"
        }
        self.updated_skill_data = {
            "technician_user": self.technician_user.user_id,
            "service": self.service.service_id,
            "experience_level": "Master"
        }

    def test_create_technicianskill(self):
        response = self.client.post('/api/technicianskills/', self.skill_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TechnicianSkill.objects.count(), 1)
        self.assertEqual(TechnicianSkill.objects.get().experience_level, 'Expert')

    def test_get_all_technicianskills(self):
        TechnicianSkill.objects.create(
            technician_user=self.technician_user, service=self.service, experience_level="Beginner"
        )
        response = self.client.get('/api/technicianskills/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_single_technicianskill(self):
        skill = TechnicianSkill.objects.create(
            technician_user=self.technician_user, service=self.service, experience_level="Intermediate"
        )
        response = self.client.get(f'/api/technicianskills/{skill.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['experience_level'], 'Intermediate')

    def test_update_technicianskill(self):
        skill = TechnicianSkill.objects.create(
            technician_user=self.technician_user, service=self.service, experience_level="Journeyman"
        )
        response = self.client.put(f'/api/technicianskills/{skill.id}/', self.updated_skill_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        skill.refresh_from_db()
        self.assertEqual(skill.experience_level, 'Master')

    def test_delete_technicianskill(self):
        skill = TechnicianSkill.objects.create(
            technician_user=self.technician_user, service=self.service, experience_level="Apprentice"
        )
        response = self.client.delete(f'/api/technicianskills/{skill.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TechnicianSkill.objects.count(), 0)


class VerificationDocumentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usertype = UserType.objects.create(user_type_name="Technician")
        self.technician_user = User.objects.create(
            user_type=self.usertype,
            first_name="Doc", last_name="User", email="docuser@example.com",
            password="docuserpassword", registration_date=timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0)), phone_number="2233445566",
            username="docuser"
        )
        self.doc_data = {
            "technician_user": self.technician_user.user_id,
            "document_type": "ID Card",
            "document_url": "http://example.com/id_card.pdf",
            "upload_date": "2025-01-01",
            "verification_status": "Pending",
            "rejection_reason": ""
        }
        self.updated_doc_data = {
            "technician_user": self.technician_user.user_id,
            "document_type": "Passport",
            "document_url": "http://example.com/passport.pdf",
            "upload_date": "2025-01-02",
            "verification_status": "Approved",
            "rejection_reason": ""
        }

    def test_create_verificationdocument(self):
        response = self.client.post('/api/verificationdocuments/', self.doc_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VerificationDocument.objects.count(), 1)
        self.assertEqual(VerificationDocument.objects.get().document_type, 'ID Card')

    def test_get_all_verificationdocuments(self):
        VerificationDocument.objects.create(
            technician_user=self.technician_user, document_type="License",
            document_url="http://example.com/license.pdf", upload_date="2025-01-01",
            verification_status="Pending"
        )
        response = self.client.get('/api/verificationdocuments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_single_verificationdocument(self):
        doc = VerificationDocument.objects.create(
            technician_user=self.technician_user, document_type="Certificate",
            document_url="http://example.com/cert.pdf", upload_date="2025-01-01",
            verification_status="Pending"
        )
        response = self.client.get(f'/api/verificationdocuments/{doc.doc_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['document_type'], 'Certificate')

    def test_update_verificationdocument(self):
        doc = VerificationDocument.objects.create(
            technician_user=self.technician_user, document_type="Old ID",
            document_url="http://example.com/old_id.pdf", upload_date="2025-01-01",
            verification_status="Pending"
        )
        response = self.client.put(f'/api/verificationdocuments/{doc.doc_id}/', self.updated_doc_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        doc.refresh_from_db()
        self.assertEqual(doc.document_type, 'Passport')

    def test_delete_verificationdocument(self):
        doc = VerificationDocument.objects.create(
            technician_user=self.technician_user, document_type="Temp Doc",
            document_url="http://example.com/temp.pdf", upload_date="2025-01-01",
            verification_status="Pending"
        )
        response = self.client.delete(f'/api/verificationdocuments/{doc.doc_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(VerificationDocument.objects.count(), 0)


class OrderAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create UserTypes
        self.client_usertype = UserType.objects.create(user_type_name="Customer")
        self.tech_usertype = UserType.objects.create(user_type_name="Technician")

        # Create Users
        self.client_user = User.objects.create(
            user_type=self.client_usertype, first_name="Client", last_name="User",
            email="clientuser@example.com", password="clientpassword",
            registration_date=timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0)), phone_number="3344556677", username="clientuser"
        )
        self.technician_user = User.objects.create(
            user_type=self.tech_usertype, first_name="Order", last_name="Tech",
            email="ordertech@example.com", password="ordertechpassword",
            registration_date=timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0)), phone_number="4455667788", username="ordertech"
        )

        # Create ServiceCategory and Service
        self.category = ServiceCategory.objects.create(category_name="OrderTestCategory", description="Category for order test")
        self.service = Service.objects.create(
            category=self.category, service_name="OrderTestService", description="Service for order test",
            service_type="Repair", base_inspection_fee=60.00
        )

        self.order_data = {
            "client_user": self.client_user.user_id,
            "service": self.service.service_id,
            "technician_user": self.technician_user.user_id,
            "order_type": "Emergency",
            "problem_description": "Leaky faucet in kitchen.",
            "requested_location": "123 Main St, Anytown",
            "scheduled_date": "2025-02-01",
            "scheduled_time_start": "10:00",
            "scheduled_time_end": "12:00",
            "order_status": "Pending",
            "creation_timestamp": "2025-01-30",
            "final_price": 150.00,
            "commission_percentage": 10.00,
            "platform_commission_amount": 15.00,
            "service_fee_percentage": 5.00,
            "service_fee_amount": 7.50,
            "total_amount_paid_by_client": 157.50,
            "amount_to_technician": 135.00
        }
        self.updated_order_data = {
            "client_user": self.client_user.user_id,
            "service": self.service.service_id,
            "technician_user": self.technician_user.user_id,
            "order_type": "Scheduled",
            "problem_description": "Fixed leaky faucet in kitchen.",
            "requested_location": "123 Main St, Anytown",
            "scheduled_date": "2025-02-01",
            "scheduled_time_start": "10:00",
            "scheduled_time_end": "12:00",
            "order_status": "Completed",
            "creation_timestamp": "2025-01-30",
            "job_start_timestamp": "2025-02-01",
            "job_completion_timestamp": "2025-02-01",
            "final_price": 160.00,
            "commission_percentage": 10.00,
            "platform_commission_amount": 16.00,
            "service_fee_percentage": 5.00,
            "service_fee_amount": 8.00,
            "total_amount_paid_by_client": 168.00,
            "amount_to_technician": 144.00
        }

    def test_create_order(self):
        response = self.client.post('/api/orders/', self.order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.get().problem_description, 'Leaky faucet in kitchen.')

    def test_get_all_orders(self):
        Order.objects.create(
            client_user=self.client_user, service=self.service, technician_user=self.technician_user,
            order_type="Scheduled", problem_description="Another order", requested_location="456 Oak Ave",
            scheduled_date="2025-03-01", scheduled_time_start="09:00", scheduled_time_end="11:00",
            order_status="Pending", creation_timestamp="2025-02-28"
        )
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_single_order(self):
        order = Order.objects.create(
            client_user=self.client_user, service=self.service, technician_user=self.technician_user,
            order_type="Emergency", problem_description="Single order", requested_location="789 Pine St",
            scheduled_date="2025-04-01", scheduled_time_start="13:00", scheduled_time_end="15:00",
            order_status="Pending", creation_timestamp="2025-03-30"
        )
        response = self.client.get(f'/api/orders/{order.order_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['problem_description'], 'Single order')

    def test_update_order(self):
        order = Order.objects.create(
            client_user=self.client_user, service=self.service, technician_user=self.technician_user,
            order_type="Emergency", problem_description="Original order", requested_location="101 Elm St",
            scheduled_date="2025-05-01", scheduled_time_start="08:00", scheduled_time_end="10:00",
            order_status="Pending", creation_timestamp="2025-04-30"
        )
        response = self.client.put(f'/api/orders/{order.order_id}/', self.updated_order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'Completed')

    def test_delete_order(self):
        order = Order.objects.create(
            client_user=self.client_user, service=self.service, technician_user=self.technician_user,
            order_type="Scheduled", problem_description="Order to delete", requested_location="202 Birch Ln",
            scheduled_date="2025-06-01", scheduled_time_start="14:00", scheduled_time_end="16:00",
            order_status="Pending", creation_timestamp="2025-05-30"
        )
        response = self.client.delete(f'/api/orders/{order.order_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Order.objects.count(), 0)
