from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from ..models import VerificationDocument
from users.models import User, UserType
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
import datetime

class VerificationDocumentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
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

        self.document = VerificationDocument.objects.create(
            technician_user=self.technician_user,
            document_type='ID',
            document_url='http://example.com/id.pdf',
            upload_date=datetime.date.today(),
            verification_status='Pending'
        )
        self.other_document = VerificationDocument.objects.create(
            technician_user=self.other_technician_user,
            document_type='Passport',
            document_url='http://example.com/passport.pdf',
            upload_date=datetime.date.today(),
            verification_status='Approved'
        )

        self.doc_data = {
            'technician_user': self.technician_user.user_id,
            'document_type': 'License',
            'document_url': 'http://example.com/license.pdf',
            'upload_date': str(datetime.date.today()),
            'verification_status': 'Pending'
        }

        self.list_url = reverse('verificationdocument-list')
        self.detail_url = reverse('verificationdocument-detail', args=[self.document.doc_id])
        self.other_detail_url = reverse('verificationdocument-detail', args=[self.other_document.doc_id])

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    def test_create_doc_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, self.doc_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_doc_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.post(self.list_url, self.doc_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_own_doc_technician(self):
        client = self.get_auth_client(self.technician_user)
        response = client.post(self.list_url, self.doc_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VerificationDocument.objects.count(), 3)

    def test_create_doc_for_other_technician_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        doc_data_for_other = self.doc_data.copy()
        doc_data_for_other['technician_user'] = self.other_technician_user.user_id
        response = client.post(self.list_url, doc_data_for_other, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_doc_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.list_url, self.doc_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_docs_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_docs_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_own_docs_technician(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_docs_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_doc_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_doc_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_own_doc_technician(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_other_doc_technician_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.get(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_doc_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_doc_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.patch(self.detail_url, {'verification_status': 'Approved'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_doc_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.patch(self.detail_url, {'verification_status': 'Approved'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_own_doc_technician(self):
        client = self.get_auth_client(self.technician_user)
        response = client.patch(self.detail_url, {'document_type': 'Updated ID'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.document.refresh_from_db()
        self.assertEqual(self.document.document_type, 'Updated ID')

    def test_update_other_doc_technician_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.patch(self.other_detail_url, {'verification_status': 'Rejected'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_doc_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.patch(self.detail_url, {'verification_status': 'Approved'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.document.refresh_from_db()
        self.assertEqual(self.document.verification_status, 'Approved')

    def test_delete_doc_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_doc_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_doc_technician(self):
        client = self.get_auth_client(self.technician_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(VerificationDocument.objects.filter(pk=self.document.pk).exists())

    def test_delete_other_doc_technician_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.delete(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_doc_admin(self):
        client = self.get_auth_client(self.admin_user)
        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(VerificationDocument.objects.filter(pk=self.document.pk).exists())
