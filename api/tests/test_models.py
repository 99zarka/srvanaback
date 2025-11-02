from django.test import TestCase
from api.models import UserType, User, ServiceCategory, Service, Order, Address, Conversation, Message, IssueReport, NotificationPreference, Notification, PaymentMethod, Review, TechnicianAvailability, TechnicianSkill, VerificationDocument, Transaction
from api.models.orders.attachments import Media
from api.models.orders.feedback import Complaint, ProjectOffer
from api.models.orders.transactions import Payment
from django.utils import timezone
from datetime import date, datetime, timedelta

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
            registration_date=timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0)),
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

        # Create an Address
        self.address = Address.objects.create(
            user=self.user,
            street_address="456 Oak Ave",
            city="Anytown",
            state="CA",
            zip_code="90210",
            country="USA",
            is_default=True
        )

        # Create a Technician User
        self.technician_user_type = UserType.objects.create(user_type_name="Technician")
        self.technician_user = User.objects.create(
            user_type=self.technician_user_type,
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            phone_number="0987654321",
            password="anothersecurepassword",
            registration_date=timezone.make_aware(datetime(2025, 1, 1, 0, 0, 0)),
            username="janesmith",
            account_status="Active"
        )

        # Update the order with a technician
        self.order.technician_user = self.technician_user
        self.order.save()

        # Create a Conversation
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user, self.technician_user)

        # Create a Message
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user,
            content="Hello, I need help with my pipe."
        )

        # Create an IssueReport
        self.issue_report = IssueReport.objects.create(
            reporter=self.user,
            order=self.order,
            title="Pipe still leaking",
            description="The pipe repair did not fix the leak.",
            status="open",
            priority="high"
        )

        # Create NotificationPreference
        self.notification_preference = NotificationPreference.objects.create(
            user=self.user,
            email_notifications=True,
            sms_notifications=False,
            push_notifications=True,
            promotional_notifications=False
        )

        # Create Notification
        self.notification = Notification.objects.create(
            user=self.user,
            title="Order Update",
            message="Your order #123 has been updated."
        )

        # Create PaymentMethod
        self.payment_method = PaymentMethod.objects.create(
            user=self.user,
            card_type="Visa",
            last_four_digits="1111",
            expiration_date="12/2028",
            card_holder_name="John Doe",
            is_default=True
        )

        # Create Review
        self.review = Review.objects.create(
            order=self.order,
            reviewer=self.user,
            technician=self.technician_user,
            rating=5,
            comment="Excellent service!"
        )

        # Create TechnicianAvailability
        self.technician_availability = TechnicianAvailability.objects.create(
            technician_user=self.technician_user,
            day_of_week="Monday",
            start_time="09:00",
            end_time="17:00",
            is_available=True,
            hourly_rate=75.00,
            experience_years=5
        )

        # Create TechnicianSkill
        self.technician_skill = TechnicianSkill.objects.create(
            technician_user=self.technician_user,
            service=self.service,
            experience_level="Expert"
        )

        # Create VerificationDocument
        self.verification_document = VerificationDocument.objects.create(
            technician_user=self.technician_user,
            document_type="ID Card",
            document_url="http://example.com/id.pdf",
            upload_date=date.today(),
            verification_status="Approved"
        )

        # Create Transaction
        self.transaction = Transaction.objects.create(
            user=self.user,
            order=self.order,
            transaction_type="payment",
            amount=150.00,
            currency="USD",
            status="completed",
            transaction_id="txn_12345"
        )

        # Create Media
        self.media = Media.objects.create(
            order=self.order,
            client_user=self.user,
            media_url="http://example.com/image.jpg",
            media_type="image",
            upload_date=date.today(),
            context="Before repair"
        )

        # Create Complaint
        self.complaint = Complaint.objects.create(
            order=self.order,
            client_user=self.user,
            technician_user=self.technician_user,
            complaint_details="Technician was late.",
            submission_date=date.today(),
            status="pending"
        )

        # Create ProjectOffer
        self.project_offer = ProjectOffer.objects.create(
            order=self.order,
            technician_user=self.technician_user,
            offered_price=120.00,
            offer_description="I can fix it quickly.",
            offer_date=date.today(),
            status="pending"
        )

        # Create Payment
        self.payment = Payment.objects.create(
            order=self.order,
            client_user=self.user,
            payment_method="Credit Card",
            transaction_id="pay_67890",
            amount=150.00,
            payment_date=date.today(),
            payment_status="completed",
            is_deposit=False
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

    def test_address_creation(self):
        address = Address.objects.get(user=self.user, street_address="456 Oak Ave")
        self.assertEqual(address.city, "Anytown")
        self.assertTrue(address.is_default)

    def test_conversation_creation(self):
        conversation = Conversation.objects.get(id=self.conversation.id)
        self.assertIn(self.user, conversation.participants.all())
        self.assertIn(self.technician_user, conversation.participants.all())

    def test_message_creation(self):
        message = Message.objects.get(conversation=self.conversation, sender=self.user)
        self.assertEqual(message.content, "Hello, I need help with my pipe.")
        self.assertFalse(message.is_read)

    def test_issue_report_creation(self):
        issue_report = IssueReport.objects.get(reporter=self.user, order=self.order)
        self.assertEqual(issue_report.title, "Pipe still leaking")
        self.assertEqual(issue_report.status, "open")
        self.assertEqual(issue_report.priority, "high")

    def test_notification_preference_creation(self):
        notification_preference = NotificationPreference.objects.get(user=self.user)
        self.assertTrue(notification_preference.email_notifications)
        self.assertFalse(notification_preference.sms_notifications)

    def test_notification_creation(self):
        notification = Notification.objects.get(user=self.user, title="Order Update")
        self.assertEqual(notification.message, "Your order #123 has been updated.")
        self.assertFalse(notification.is_read)

    def test_payment_method_creation(self):
        payment_method = PaymentMethod.objects.get(user=self.user, last_four_digits="1111")
        self.assertEqual(payment_method.card_type, "Visa")
        self.assertTrue(payment_method.is_default)

    def test_review_creation(self):
        review = Review.objects.get(order=self.order, reviewer=self.user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Excellent service!")
        self.assertEqual(review.technician, self.technician_user)

    def test_technician_availability_creation(self):
        availability = TechnicianAvailability.objects.get(technician_user=self.technician_user, day_of_week="Monday")
        self.assertEqual(availability.start_time, "09:00")
        self.assertTrue(availability.is_available)

    def test_technician_skill_creation(self):
        skill = TechnicianSkill.objects.get(technician_user=self.technician_user, service=self.service)
        self.assertEqual(skill.experience_level, "Expert")

    def test_verification_document_creation(self):
        document = VerificationDocument.objects.get(technician_user=self.technician_user, document_type="ID Card")
        self.assertEqual(document.verification_status, "Approved")
        self.assertEqual(document.document_url, "http://example.com/id.pdf")

    def test_transaction_creation(self):
        transaction = Transaction.objects.get(user=self.user, transaction_id="txn_12345")
        self.assertEqual(transaction.amount, 150.00)
        self.assertEqual(transaction.status, "completed")
        self.assertEqual(transaction.transaction_type, "payment")

    def test_media_creation(self):
        media = Media.objects.get(order=self.order, client_user=self.user)
        self.assertEqual(media.media_type, "image")
        self.assertEqual(media.media_url, "http://example.com/image.jpg")

    def test_complaint_creation(self):
        complaint = Complaint.objects.get(order=self.order, client_user=self.user)
        self.assertEqual(complaint.complaint_details, "Technician was late.")
        self.assertEqual(complaint.status, "pending")

    def test_project_offer_creation(self):
        project_offer = ProjectOffer.objects.get(order=self.order, technician_user=self.technician_user)
        self.assertEqual(project_offer.offered_price, 120.00)
        self.assertEqual(project_offer.status, "pending")

    def test_payment_creation(self):
        payment = Payment.objects.get(order=self.order, client_user=self.user)
        self.assertEqual(payment.amount, 150.00)
        self.assertEqual(payment.payment_status, "completed")
        self.assertFalse(payment.is_deposit)
