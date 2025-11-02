from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, datetime
from django.utils import timezone
from api.models import (
    UserType, User, ServiceCategory, Service, Order,
    TechnicianSkill, TechnicianAvailability, VerificationDocument
)
from rest_framework_simplejwt.tokens import RefreshToken

class TechnicianSkillAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usertype, created = UserType.objects.get_or_create(user_type_id=1, user_type_name="Customer")
        self.register_url = '/api/register/'

        # Register a user and get tokens
        self.user_data = {
            "email": "skilluser@example.com",
            "username": "skilluser",
            "password": "skillpassword123",
            "password2": "skillpassword123",
            "first_name": "Skill",
            "last_name": "User",
            "phone_number": "4444444444",
            "address": "4 Skill St",
            # user_type is now optional and defaults to 1 in the model
        }
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.access_token = response.data['tokens']['access']

        # Authenticate the client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

        self.technician_user = User.objects.create(
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

    def test_create_technicianskill_authenticated(self):
        response = self.client.post('/api/technicianskills/', self.skill_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TechnicianSkill.objects.count(), 1)
        self.assertEqual(TechnicianSkill.objects.get().experience_level, 'Expert')

    def test_create_technicianskill_unauthenticated(self):
        self.client.credentials() # Clear credentials
        response = self.client.post('/api/technicianskills/', self.skill_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_technicianskills_authenticated(self):
        TechnicianSkill.objects.create(
            technician_user=self.technician_user, service=self.service, experience_level="Beginner"
        )
        response = self.client.get('/api/technicianskills/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_single_technicianskill_authenticated(self):
        skill = TechnicianSkill.objects.create(
            technician_user=self.technician_user, service=self.service, experience_level="Intermediate"
        )
        response = self.client.get(f'/api/technicianskills/{skill.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['experience_level'], 'Intermediate')

    def test_update_technicianskill_authenticated(self):
        skill = TechnicianSkill.objects.create(
            technician_user=self.technician_user, service=self.service, experience_level="Journeyman"
        )
        response = self.client.put(f'/api/technicianskills/{skill.id}/', self.updated_skill_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        skill.refresh_from_db()
        self.assertEqual(skill.experience_level, 'Master')

    def test_delete_technicianskill_authenticated(self):
        skill = TechnicianSkill.objects.create(
            technician_user=self.technician_user, service=self.service, experience_level="Apprentice"
        )
        response = self.client.delete(f'/api/technicianskills/{skill.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TechnicianSkill.objects.count(), 0)
