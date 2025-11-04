from rest_framework import viewsets, generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .permissions import (
    IsAdminUser, IsClientUser, IsTechnicianUser,
    IsClientOrTechnicianUser, IsAdminOrTechnicianUser,
    IsOwnerOrAdmin, IsClientOwnerOrAdmin, IsTechnicianOwnerOrAdmin, IsUserOwnerOrAdmin,
    IsConversationParticipantOrAdmin, IsMessageSenderOrAdmin, IsReviewOwnerOrAdmin,
    IsReviewTechnicianOrAdmin, IsAuthenticatedOrReadOnly
)
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
from rest_framework import serializers

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

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        else: # list, retrieve
            self.permission_classes = [permissions.AllowAny] # Publicly accessible
        return super().get_permissions()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == 'list':
            self.permission_classes = [permissions.IsAuthenticated] # Only authenticated users can list
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsOwnerOrAdmin)] # Only admin or owner can retrieve/update/delete
        elif self.action == 'create':
            self.permission_classes = [IsAdminUser | permissions.AllowAny] # Allow any user to create an account (handled by RegisterView)
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        # Admins can see all users
        if user.is_authenticated and user.user_type.user_type_name == 'admin':
            return User.objects.all()
        # Other authenticated users can only see their own profile for list action
        if user.is_authenticated:
            if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
                return User.objects.all() # For detail actions, return all objects and let object-level permissions handle filtering
            return User.objects.filter(user_id=user.user_id)
        return User.objects.none() # Unauthenticated users cannot see any users

class ServiceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        else: # list, retrieve
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        else: # list, retrieve
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

class TechnicianAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = TechnicianAvailability.objects.all()
    serializer_class = TechnicianAvailabilitySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
        else: # list, retrieve
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        # Allow unauthenticated users to view all availability
        if self.request.method in permissions.SAFE_METHODS and not user.is_authenticated:
            return TechnicianAvailability.objects.all()
        # Admins can see all availability
        if user.is_authenticated and user.user_type.user_type_name == 'admin':
            return TechnicianAvailability.objects.all()
        # Technicians can only see their own availability
        if user.is_authenticated and user.user_type.user_type_name == 'technician':
            return TechnicianAvailability.objects.filter(technician_user=user)
        # Clients can view all availability
        if user.is_authenticated and user.user_type.user_type_name == 'client':
            return TechnicianAvailability.objects.all()
        return TechnicianAvailability.objects.none() # Should not be reached if permissions are set correctly

class TechnicianSkillViewSet(viewsets.ModelViewSet):
    queryset = TechnicianSkill.objects.all()
    serializer_class = TechnicianSkillSerializer

    def get_permissions(self):
        if self.action == 'create':
            # For create action, check if a technician is trying to create a skill for another technician
            user = self.request.user
            if user.is_authenticated and user.user_type.user_type_name == 'technician':
                requested_technician_user_id = self.request.data.get('technician_user')
                if requested_technician_user_id and requested_technician_user_id != user.user_id:
                    raise PermissionDenied("Technicians can only create skills for themselves.")
            self.permission_classes = [IsAdminUser | IsTechnicianUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
        else: # list, retrieve
            self.permission_classes = [IsAuthenticatedOrReadOnly]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.user_type.user_type_name == 'admin':
                return TechnicianSkill.objects.all()
            elif user.user_type.user_type_name == 'technician':
                if self.action == 'list':
                    return TechnicianSkill.objects.filter(technician_user=user)
                # For detail actions, return all objects and let object-level permissions handle filtering
                return TechnicianSkill.objects.all()
        # For unauthenticated users or clients, allow viewing all skills (publicly accessible)
        # For other actions (create, update, delete) for non-admin/non-technician, permissions will handle it.
        return TechnicianSkill.objects.all() if self.request.method in permissions.SAFE_METHODS else TechnicianSkill.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_authenticated:
            if user.user_type.user_type_name == 'technician':
                serializer.save(technician_user=user)
            elif user.user_type.user_type_name == 'admin':
                # Admins can create skills for any technician, so technician_user must be provided
                if 'technician_user' not in self.request.data:
                    raise serializers.ValidationError({"technician_user": "This field is required for admin users."})
                serializer.save()
            else:
                raise PermissionDenied("Only technicians and admins can create skills.")
        else:
            raise PermissionDenied("Authentication required to create skills.")

class VerificationDocumentViewSet(viewsets.ModelViewSet):
    queryset = VerificationDocument.objects.all()
    serializer_class = VerificationDocumentSerializer

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAdminUser | IsTechnicianUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
        else: # list, retrieve
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.user_type.user_type_name == 'admin':
                return VerificationDocument.objects.all()
            elif user.user_type.user_type_name == 'technician':
                if self.action == 'list':
                    return VerificationDocument.objects.filter(technician_user=user)
                return VerificationDocument.objects.all() # For detail actions, return all objects and let object-level permissions handle filtering
        return VerificationDocument.objects.none() # Unauthenticated users cannot see any documents

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_authenticated and user.user_type.user_type_name == 'technician':
            requested_technician_user_id = self.request.data.get('technician_user')
            if requested_technician_user_id and requested_technician_user_id != user.user_id:
                raise PermissionDenied("Technicians can only create verification documents for themselves.")
            serializer.save(technician_user=user)
        elif user.is_authenticated and user.user_type.user_type_name == 'admin':
            if 'technician_user' not in self.request.data:
                raise serializers.ValidationError({"technician_user": "This field is required for admin users."})
            serializer.save()
        else:
            raise PermissionDenied("Only technicians and admins can create verification documents.")

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser | (IsClientUser & IsClientOwnerOrAdmin) | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.user_type.user_type_name == 'client':
            return Order.objects.filter(client_user=self.request.user)
        elif self.request.user.is_authenticated and self.request.user.user_type.user_type_name == 'technician':
            return Order.objects.filter(technician_user=self.request.user)
        return super().get_queryset()

class ProjectOfferViewset(viewsets.ModelViewSet):
    queryset = ProjectOffer.objects.all()
    serializer_class = ProjectOfferSerializer

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAdminUser | IsTechnicianUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
        else: # list, retrieve
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin) | (IsClientUser & IsClientOwnerOrAdmin)]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.user_type.user_type_name == 'admin':
                return ProjectOffer.objects.all()
            elif user.user_type.user_type_name == 'technician':
                if self.action == 'list':
                    return ProjectOffer.objects.filter(technician_user=user)
                return ProjectOffer.objects.all() # For detail actions, return all objects and let object-level permissions handle filtering
            elif user.user_type.user_type_name == 'client':
                if self.action == 'list':
                    return ProjectOffer.objects.filter(order__client_user=user) # Clients can see offers related to their orders
                return ProjectOffer.objects.all() # For detail actions, return all objects and let object-level permissions handle filtering
        return ProjectOffer.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_authenticated and user.user_type.user_type_name == 'technician':
            # Ensure the technician_user in the offer data matches the authenticated technician
            requested_technician_user_id = self.request.data.get('technician_user')
            if requested_technician_user_id and requested_technician_user_id != user.user_id:
                raise PermissionDenied("Technicians can only create offers for themselves.")
            serializer.save(technician_user=user)
        elif user.is_authenticated and user.user_type.user_type_name == 'admin':
            # Admins can create offers for any technician, so technician_user must be provided in data
            if 'technician_user' not in self.request.data:
                raise serializers.ValidationError({"technician_user": "This field is required for admin users."})
            serializer.save()
        else:
            raise PermissionDenied("Only technicians and admins can create project offers.")

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAdminUser | (IsClientUser & IsUserOwnerOrAdmin)]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.user_type.user_type_name == 'admin':
            return Address.objects.all()
        elif self.request.user.is_authenticated:
            if self.action in ['list', 'create']:
                return Address.objects.filter(user=self.request.user)
            # For detail actions, return all objects and let object-level permissions handle filtering
            return Address.objects.all()
        return super().get_queryset()

class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAdminUser | ((IsClientUser | IsTechnicianUser) & IsUserOwnerOrAdmin)]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.user_type.user_type_name == 'admin':
                return PaymentMethod.objects.all()
            elif user.user_type.user_type_name in ['client', 'technician']:
                return PaymentMethod.objects.filter(user=user)
            else:
                return PaymentMethod.objects.none()
        return PaymentMethod.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_authenticated and user.user_type.user_type_name in ['client', 'technician']:
            if 'user' in self.request.data and self.request.data['user'] != user.user_id:
                raise PermissionDenied("Users can only create payment methods for themselves.")
            serializer.save(user=user)
        elif user.is_authenticated and user.user_type.user_type_name == 'admin':
            if 'user' not in self.request.data:
                raise serializers.ValidationError({"user": "This field is required for admin users."})
            serializer.save()
        else:
            raise PermissionDenied("Only clients, technicians, and admins can create payment methods.")

class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    queryset = NotificationPreference.objects.all()
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAdminUser | (IsClientUser & IsUserOwnerOrAdmin)]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.user_type.user_type_name == 'admin':
                return NotificationPreference.objects.all()
            elif self.request.user.user_type.user_type_name == 'technician':
                return NotificationPreference.objects.none() # Technicians should not access notification preferences
            else: # Client user
                # For detail actions, return all objects and let object-level permissions handle filtering
                if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
                    return NotificationPreference.objects.all()
                # For list actions, return only preferences belonging to the authenticated user
                return NotificationPreference.objects.filter(user=self.request.user)
        return super().get_queryset()

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_authenticated and user.user_type.user_type_name == 'client':
            # Clients can only create payment methods for themselves
            if 'user' in self.request.data and self.request.data['user'] != user.user_id:
                raise permissions.PermissionDenied("Clients can only create payment methods for themselves.")
            serializer.save(user=user)
        elif user.is_authenticated and user.user_type.user_type_name == 'admin':
            # Admins can create payment methods for any user, so 'user' field is required
            if 'user' not in self.request.data:
                raise serializers.ValidationError({"user": "This field is required for admin users."})
            serializer.save()
        else:
            # Other user types (e.g., technicians) should be forbidden by permission_classes
            raise permissions.PermissionDenied("Only clients and admins can create payment methods.")

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsUserOwnerOrAdmin)]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.user_type.user_type_name == 'admin':
            return Notification.objects.all()
        elif self.request.user.is_authenticated:
            return Notification.objects.filter(user=self.request.user)
        return super().get_queryset()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # Ensure that the user field is not updated during a PATCH/PUT request
        if 'user' in serializer.validated_data:
            serializer.validated_data.pop('user')
        serializer.save()

    def perform_update(self, serializer):
        # Ensure that the user field is not updated during a PATCH/PUT request
        if 'user' in serializer.validated_data:
            serializer.validated_data.pop('user')
        serializer.save()

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAdminUser | IsClientUser | IsTechnicianUser] # Only clients, technicians, and admins can create reviews
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (IsClientUser & IsReviewOwnerOrAdmin)] # Only admin or client owner can update/delete
        else: # list, retrieve
            self.permission_classes = [IsAdminUser | (IsClientUser & IsReviewOwnerOrAdmin) | (IsTechnicianUser & IsReviewTechnicianOrAdmin)] # Only authenticated users can view reviews
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.user_type.user_type_name == 'admin':
                return Review.objects.all()
            elif user.user_type.user_type_name == 'client':
                # Clients can see reviews they made or reviews for technicians they hired
                return Review.objects.filter(reviewer=user) | Review.objects.filter(technician__in=user.client_orders.values_list('technician_user', flat=True))
            elif user.user_type.user_type_name == 'technician':
                # Technicians can see reviews they received or reviews they made (as a client)
                return Review.objects.filter(technician=user) | Review.objects.filter(reviewer=user)
        return Review.objects.none() # Unauthenticated users cannot list/retrieve reviews

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_authenticated and user.user_type.user_type_name == 'client':
            # Ensure the client_user in the review data matches the authenticated client
            requested_client_user_id = self.request.data.get('reviewer') # Changed to 'reviewer'
            if requested_client_user_id and requested_client_user_id != user.user_id:
                raise PermissionDenied("Clients can only create reviews for themselves.")
            serializer.save(reviewer=user)
        elif user.is_authenticated and user.user_type.user_type_name == 'technician':
            # Technicians can create reviews for services they ordered (acting as a client)
            # Technicians can create reviews for services they ordered (acting as a client)
            # Ensure the reviewer in the review data matches the authenticated technician
            requested_reviewer_id = self.request.data.get('reviewer')
            if requested_reviewer_id and requested_reviewer_id != user.user_id:
                raise PermissionDenied("Technicians can only create reviews for themselves (as a client).")
            # Ensure technician and order are provided when a technician creates a review
            if 'technician' not in self.request.data or 'order' not in self.request.data:
                raise serializers.ValidationError({"detail": "Technician and order fields are required when a technician creates a review."})
            serializer.save(reviewer=user)
        elif user.is_authenticated and user.user_type.user_type_name == 'admin':
            # Admins can create reviews for any client/technician, so reviewer and technician must be provided
            if 'reviewer' not in self.request.data or 'technician' not in self.request.data:
                raise serializers.ValidationError({"detail": "Reviewer and technician fields are required for admin users."})
            serializer.save()
        else:
            raise PermissionDenied("Only clients, technicians, and admins can create reviews.")
class IssueReportViewSet(viewsets.ModelViewSet):
    queryset = IssueReport.objects.all()
    serializer_class = IssueReportSerializer
    permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsUserOwnerOrAdmin)]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.user_type.user_type_name == 'admin':
            return IssueReport.objects.all()
        elif self.request.user.is_authenticated:
            if self.action in ['list', 'create']:
                return IssueReport.objects.filter(reporter=self.request.user)
            # For detail actions, return all objects and let object-level permissions handle filtering
            return IssueReport.objects.all()
        return super().get_queryset()

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsUserOwnerOrAdmin)]
        else: # list, retrieve
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsUserOwnerOrAdmin)]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.user_type.user_type_name == 'admin':
                return Transaction.objects.all()
            # For detail actions, return all objects and let object-level permissions handle filtering
            if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
                return Transaction.objects.all()
            # For list actions, return only transactions belonging to the authenticated user
            return Transaction.objects.filter(user=user)
        return Transaction.objects.none() # Unauthenticated users cannot see any transactions

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsConversationParticipantOrAdmin)]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.user_type.user_type_name == 'admin':
            return Conversation.objects.all()
        elif self.request.user.is_authenticated:
            # For detail actions, return all objects and let object-level permissions handle filtering
            if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
                return Conversation.objects.all()
            # For list actions, return only conversations the user is a participant of
            return Conversation.objects.filter(participants=self.request.user)
        return super().get_queryset()

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsMessageSenderOrAdmin)]
        else: # list, retrieve, create
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsConversationParticipantOrAdmin)]
        return super().get_permissions()

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.user_type.user_type_name == 'admin':
            return Message.objects.all()
        elif self.request.user.is_authenticated:
            # For detail actions, return all objects and let object-level permissions handle filtering
            if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
                return Message.objects.all()
            # For list actions, return only messages from conversations the user is a participant of
            return Message.objects.filter(conversation__participants=self.request.user)
        return super().get_queryset()
