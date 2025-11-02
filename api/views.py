from rest_framework import viewsets, generics, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models.users import User, UserType
from .models.services import ServiceCategory, Service
from .models.technicians import TechnicianAvailability, TechnicianSkill, VerificationDocument
from .models.orders.core import Order
from .models.orders.feedback import ProjectOffer
from .models.addresses import Address
from .models.payment_methods import PaymentMethod
from .models.notifications import NotificationPreference, Notification
from .models.reviews import Review
from .models.issue_reports import IssueReport
from .models.transactions import Transaction
from .models.chat import Conversation, Message
from .serializers import (
    UserTypeSerializer, UserSerializer, UserRegistrationSerializer,
    ServiceCategorySerializer, ServiceSerializer,
    TechnicianAvailabilitySerializer, TechnicianSkillSerializer,
    VerificationDocumentSerializer, OrderSerializer, ProjectOfferSerializer,
    AddressSerializer, PaymentMethodSerializer, NotificationPreferenceSerializer,
    NotificationSerializer, ReviewSerializer, IssueReportSerializer,
    TransactionSerializer, ConversationSerializer, MessageSerializer
)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens for the newly registered user
        token_serializer = TokenObtainPairSerializer(data={
            'email': request.data['email'],
            'password': request.data['password']
        })
        token_serializer.is_valid(raise_exception=True)
        tokens = token_serializer.validated_data

        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "message": "User Created Successfully.",
            "tokens": tokens
        }, status=status.HTTP_201_CREATED)

class UserTypeViewSet(viewsets.ModelViewSet):
    queryset = UserType.objects.all()
    serializer_class = UserTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class ServiceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

class TechnicianAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = TechnicianAvailability.objects.all()
    serializer_class = TechnicianAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]

class TechnicianSkillViewSet(viewsets.ModelViewSet):
    queryset = TechnicianSkill.objects.all()
    serializer_class = TechnicianSkillSerializer
    permission_classes = [permissions.IsAuthenticated]

class VerificationDocumentViewSet(viewsets.ModelViewSet):
    queryset = VerificationDocument.objects.all()
    serializer_class = VerificationDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

class ProjectOfferViewset(viewsets.ModelViewSet):
    queryset = ProjectOffer.objects.all()
    serializer_class = ProjectOfferSerializer
    permission_classes = [permissions.IsAuthenticated]

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]

class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    queryset = NotificationPreference.objects.all()
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

class IssueReportViewSet(viewsets.ModelViewSet):
    queryset = IssueReport.objects.all()
    serializer_class = IssueReportSerializer
    permission_classes = [permissions.IsAuthenticated]

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
