from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from ..models import VerificationDocument
from users.models import User, UserType
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from notifications.models import Notification
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
        self.approve_url = reverse('verificationdocument-approve', args=[self.document.doc_id])
        self.other_approve_url = reverse('verificationdocument-approve', args=[self.other_document.doc_id])
        self.reject_url = reverse('verificationdocument-reject', args=[self.document.doc_id])
        self.other_reject_url = reverse('verificationdocument-reject', args=[self.other_document.doc_id])

    def get_auth_client(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return self.client

    # ====== Basic CRUD Tests ======
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
        # Handle pagination - check results count
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)

    def test_list_docs_admin(self):
        # Debug: Check how many documents exist before the test
        total_docs = VerificationDocument.objects.count()
        debug_info = f"Total documents before admin list test: {total_docs}\n"
        
        client = self.get_auth_client(self.admin_user)
        response = client.get(self.list_url)
        debug_info += f"Response status: {response.status_code}\n"
        debug_info += f"Response data type: {type(response.data)}\n"
        
        # Handle pagination properly
        if isinstance(response.data, dict) and 'results' in response.data:
            # Paginated response
            docs = response.data['results']
            debug_info += f"Paginated response - results count: {len(docs)}\n"
            for i, doc in enumerate(docs):
                debug_info += f"Document {i+1}: ID={doc.get('doc_id')}, Type={doc.get('document_type')}, Tech User={doc.get('technician_user')}\n"
            result_count = len(docs)
        else:
            # Non-paginated response
            docs = response.data
            debug_info += f"Non-paginated response - count: {len(docs)}\n"
            for i, doc in enumerate(docs):
                debug_info += f"Document {i+1}: ID={doc.get('doc_id')}, Type={doc.get('document_type')}, Tech User={doc.get('technician_user')}\n"
            result_count = len(docs)
        
        # Write debug info to file
        with open('test_debug_output.txt', 'w') as f:
            f.write(debug_info)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result_count, 2)

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

    # ====== Verification Approval/Rejection Tests ======
    
    def test_approve_doc_unauthenticated_forbidden(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.approve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_approve_doc_technician_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.post(self.approve_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approve_doc_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.post(self.approve_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approve_doc_admin_success(self):
        # Set initial status to Pending
        self.assertEqual(self.document.verification_status, 'Pending')
        self.assertIsNone(self.technician_user.verification_status)  # Default is None
        
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.approve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response structure
        self.assertIn('message', response.data)
        self.assertIn('verification_document', response.data)
        self.assertIn('user_verification_status', response.data)
        self.assertEqual(response.data['message'], 'Verification document approved successfully')
        
        # Verify document status updated
        self.document.refresh_from_db()
        self.assertEqual(self.document.verification_status, 'Approved')
        self.assertIsNone(self.document.rejection_reason)
        
        # Verify user verification status updated
        self.technician_user.refresh_from_db()
        self.assertEqual(self.technician_user.verification_status, 'Verified')
        self.assertEqual(response.data['user_verification_status'], 'Verified')

    def test_approve_already_approved_doc_error(self):
        # Change document to already approved
        self.other_document.verification_status = 'Approved'
        self.other_document.save()
        
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.other_approve_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Document is already approved')

    def test_reject_doc_unauthenticated_forbidden(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.reject_url, {'rejection_reason': 'Invalid documents'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reject_doc_technician_forbidden(self):
        client = self.get_auth_client(self.technician_user)
        response = client.post(self.reject_url, {'rejection_reason': 'Invalid documents'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reject_doc_client_forbidden(self):
        client = self.get_auth_client(self.client_user)
        response = client.post(self.reject_url, {'rejection_reason': 'Invalid documents'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reject_doc_admin_success(self):
        self.assertEqual(self.document.verification_status, 'Pending')
        self.assertIsNone(self.technician_user.verification_status)  # Default is None
        
        rejection_reason = 'Document image is blurry and unreadable'
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.reject_url, {'rejection_reason': rejection_reason})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response structure
        self.assertIn('message', response.data)
        self.assertIn('verification_document', response.data)
        self.assertIn('user_verification_status', response.data)
        self.assertIn('rejection_reason', response.data)
        self.assertEqual(response.data['message'], 'Verification document rejected successfully')
        self.assertEqual(response.data['rejection_reason'], rejection_reason)
        
        # Verify document status updated
        self.document.refresh_from_db()
        self.assertEqual(self.document.verification_status, 'Rejected')
        self.assertEqual(self.document.rejection_reason, rejection_reason)
        
        # Verify user verification status updated to Pending for resubmission
        self.technician_user.refresh_from_db()
        self.assertEqual(self.technician_user.verification_status, 'Pending')
        self.assertEqual(response.data['user_verification_status'], 'Pending')

    def test_reject_doc_missing_reason_error(self):
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.reject_url, {})  # No rejection_reason
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Rejection reason is required')

    def test_reject_doc_empty_reason_error(self):
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.reject_url, {'rejection_reason': ''})  # Empty reason
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Rejection reason is required')

    def test_reject_already_approved_doc_error(self):
        # Change document to already approved
        self.other_document.verification_status = 'Approved'
        self.other_document.save()
        
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.other_reject_url, {'rejection_reason': 'Some reason'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Document is already approved')

    # ====== Notification Creation Tests ======
    
    def test_approve_doc_creates_notification(self):
        # Verify no notifications exist initially
        self.assertEqual(Notification.objects.count(), 0)
        
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.approve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify notification was created
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.first()
        
        self.assertEqual(notification.user, self.technician_user)
        self.assertEqual(notification.title, 'Verification Approved')
        self.assertEqual(notification.message, 'Your verification documents have been approved. You can now start receiving service requests!')
        self.assertFalse(notification.is_read)

    def test_reject_doc_creates_notification(self):
        # Verify no notifications exist initially
        self.assertEqual(Notification.objects.count(), 0)
        
        rejection_reason = 'Documents need to be resubmitted with clearer images'
        client = self.get_auth_client(self.admin_user)
        response = client.post(self.reject_url, {'rejection_reason': rejection_reason})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify notification was created
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.first()
        
        self.assertEqual(notification.user, self.technician_user)
        self.assertEqual(notification.title, 'Verification Rejected')
        expected_message = f'Your verification documents have been rejected. Reason: {rejection_reason}. Please resubmit with the required corrections.'
        self.assertEqual(notification.message, expected_message)
        self.assertFalse(notification.is_read)

    def test_multiple_approvals_create_multiple_notifications(self):
        # Create another technician for testing
        another_tech = User.objects.create_user(
            username='anothertech',
            email='another@example.com',
            password='password123',
            user_type_name=self.technician_usertype.user_type_name
        )
        another_doc = VerificationDocument.objects.create(
            technician_user=another_tech,
            document_type='License',
            document_url='http://example.com/license2.pdf',
            upload_date=datetime.date.today(),
            verification_status='Pending'
        )
        
        # Verify no notifications exist initially
        self.assertEqual(Notification.objects.count(), 0)
        
        client = self.get_auth_client(self.admin_user)
        
        # Approve first document
        response1 = client.post(self.approve_url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(Notification.objects.count(), 1)
        
        # Approve second document
        another_approve_url = reverse('verificationdocument-approve', args=[another_doc.doc_id])
        response2 = client.post(another_approve_url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(Notification.objects.count(), 2)
        
        # Verify both notifications exist
        notifications = Notification.objects.all()
        self.assertEqual(notifications[0].user, self.technician_user)
        self.assertEqual(notifications[1].user, another_tech)
