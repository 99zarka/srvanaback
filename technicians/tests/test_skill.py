from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from ..models import TechnicianSkill
from users.models import User, UserType
from services.models import Service, ServiceCategory
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

class TechnicianSkillTests(APITestCase):
    def setUp(self):
        self.client_usertype = UserType.objects.create(user_type_name='client')
        self.technician_usertype = UserType.objects.create(user_type_name='technician')
        self.admin_usertype = UserType.objects.create(user_type_name='admin')

        self.client_user = User.objects.create_user(
            username='clientuser',
            email='client@example.com',
            password='password123',
            user_type_name=self.client_usertype.user_type_name
        )
        self.technician_user = User.objects.create_user(
            username='techuser',
            email='technician@example.com',
            password='password123',
            user_type_name=self.technician_usertype.user_type_name
        )
        self.other_technician_user = User.objects.create_user(
            username='othertech',
            email='othertechnician@example.com',
            password='password123',
            user_type_name=self.technician_usertype.user_type_name
        )
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            username="adminuser",
            password="adminpassword123",
            user_type_name=self.admin_usertype.user_type_name,
        )

        self.service_category = ServiceCategory.objects.create(category_name='Electronics Repair')
        self.service = Service.objects.create(
            category=self.service_category,
            service_name='Test Service',
            description='Description for test service',
            service_type='Repair',
            base_inspection_fee=50.00
        )
        self.other_service = Service.objects.create(
            category=self.service_category,
            service_name='Other Service',
            description='Description for other service',
            service_type='Installation',
            base_inspection_fee=75.00
        )

        self.skill = TechnicianSkill.objects.create(
            technician_user=self.technician_user,
            service=self.service,
            experience_level='Intermediate'
        )
        self.other_skill = TechnicianSkill.objects.create(
            technician_user=self.other_technician_user,
            service=self.other_service,
            experience_level='Expert'
        )

        self.skill_data = {
            'technician_user': self.technician_user.user_id,
            'service': self.other_service.service_id,
            'experience_level': 'Beginner'
        }

        self.list_url = reverse('technicianskill-list')
        self.detail_url = reverse('technicianskill-detail', args=[self.skill.id])
        self.other_detail_url = reverse('technicianskill-detail', args=[self.other_skill.id])

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    def test_create_skill_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, self.skill_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_skill_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.post(self.list_url, self.skill_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_skill_technician_owner(self):
        client = self.get_auth_client(self.technician_user)
        response = client.post(self.list_url, self.skill_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TechnicianSkill.objects.count(), 3)

    def test_create_skill_for_other_technician_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        skill_data_for_other = self.skill_data.copy()
        skill_data_for_other['technician_user'] = self.other_technician_user.user_id
        response = client.post(self.list_url, skill_data_for_other, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_skill_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.list_url, self.skill_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_skills_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Publicly accessible

    def test_list_skills_authenticated(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_skill_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Publicly accessible

    def test_retrieve_skill_authenticated(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_skill_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.patch(self.detail_url, {'experience_level': 'Expert'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_skill_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.patch(self.detail_url, {'experience_level': 'Expert'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_own_skill_technician(self):
        client = self.get_auth_client(self.technician_user)
        response = client.patch(self.detail_url, {'experience_level': 'Expert'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.skill.refresh_from_db()
        self.assertEqual(self.skill.experience_level, 'Expert')

    def test_update_other_skill_technician_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.patch(self.other_detail_url, {'experience_level': 'Master'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_skill_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.patch(self.detail_url, {'experience_level': 'Master'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.skill.refresh_from_db()
        self.assertEqual(self.skill.experience_level, 'Master')

    def test_delete_skill_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_skill_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_skill_technician(self):
        client = self.get_auth_client(self.technician_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TechnicianSkill.objects.filter(pk=self.skill.pk).exists())

    def test_delete_other_skill_technician_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.delete(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_skill_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TechnicianSkill.objects.filter(pk=self.skill.pk).exists())
