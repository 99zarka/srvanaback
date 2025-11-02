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

class VerificationDocumentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.usertype, created = UserType.objects.get_or_create(user_type_id=1, user_type_name="Customer")
        self.register_url = '/api/register/'

        # Register a user and get tokens
        self.user_data = {
            "email": "docuser@example.com",
            "username": "docuser",
            "password": "docpassword123",
            "password2": "docpassword123",
            "first_name": "Doc",
            "last_name": "User",
            "phone_number": "5555555555",
            "address": "5 Doc St",
            # user_type is now optional and defaults to 1 in the model
        }
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.access_token = response.data['tokens']['access']

        # Authenticate the client
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

        self.technician_user = User.objects.create(
            first_name="Tech", last_name="User", email="techuser@example.com",
            password="techpassword123", registration_date=timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0)), phone_number="2233445566",
            username="techuser"
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

    def test_create_verificationdocument_authenticated(self):
        response = self.client.post('/api/verificationdocuments/', self.doc_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VerificationDocument.objects.count(), 1)
        self.assertEqual(VerificationDocument.objects.get().document_type, 'ID Card')

    def test_create_verificationdocument_unauthenticated(self):
        self.client.credentials() # Clear credentials
        response = self.client.post('/api/verificationdocuments/', self.doc_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_verificationdocuments_authenticated(self):
        VerificationDocument.objects.create(
            technician_user=self.technician_user, document_type="License",
            document_url="http://example.com/license.pdf", upload_date="2025-01-01",
            verification_status="Pending"
        )
        response = self.client.get('/api/verificationdocuments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_single_verificationdocument_authenticated(self):
        doc = VerificationDocument.objects.create(
            technician_user=self.technician_user, document_type="Certificate",
            document_url="http://example.com/cert.pdf", upload_date="2025-01-01",
            verification_status="Pending"
        )
        response = self.client.get(f'/api/verificationdocuments/{doc.doc_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['document_type'], 'Certificate')

    def test_update_verificationdocument_authenticated(self):
        doc = VerificationDocument.objects.create(
            technician_user=self.technician_user, document_type="Old ID",
            document_url="http://example.com/old_id.pdf", upload_date="2025-01-01",
            verification_status="Pending"
        )
        response = self.client.put(f'/api/verificationdocuments/{doc.doc_id}/', self.updated_doc_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        doc.refresh_from_db()
        self.assertEqual(doc.document_type, 'Passport')

    def test_delete_verificationdocument_authenticated(self):
        doc = VerificationDocument.objects.create(
            technician_user=self.technician_user, document_type="Temp Doc",
            document_url="http://example.com/temp.pdf", upload_date="2025-01-01",
            verification_status="Pending"
        )
        response = self.client.delete(f'/api/verificationdocuments/{doc.doc_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(VerificationDocument.objects.count(), 0)
