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

class OwnerFilteredQuerysetMixin:
    owner_field = 'user' # Default field to filter by for non-admin users

    def get_filtered_queryset(self, user, base_queryset):
        """
        Returns the queryset for non-admin authenticated users,
        filtered from the provided base_queryset.
        Can be overridden in specific ViewSets for custom filtering.
        """
        # If the owner_field is a direct foreign key to User, use the User object.
        # If it's a primary key field (like 'user_id'), use the user's primary key.
        if self.owner_field.endswith('_id'):
            filter_kwargs = {self.owner_field: user.pk}
        else:
            filter_kwargs = {self.owner_field: user}
        return base_queryset.filter(**filter_kwargs)

    def get_queryset(self):
        user = self.request.user
        base_queryset = super().get_queryset() # Get the initial queryset from the next class in MRO (e.g., ModelViewSet)

        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            # For detail actions, always return the full queryset.
            # Object-level permissions will handle access control (403 if forbidden).
            return base_queryset
        
        if user.is_authenticated and user.user_type.user_type_name == 'admin':
            return base_queryset # Admin sees all for list actions
        elif user.is_authenticated:
            return self.get_filtered_queryset(user, base_queryset) # Authenticated non-admin users get filtered for list actions
        else: # User is not authenticated
            # Check if any permission allows unauthenticated read access for list actions
            has_read_only_permission = any(isinstance(perm, permissions.AllowAny) or isinstance(perm, IsAuthenticatedOrReadOnly) for perm in self.get_permissions())
            if has_read_only_permission and self.action == 'list':
                return base_queryset # Allow unauthenticated read access for list
            # If not read-only, or not list, then no access for unauthenticated users
            return base_queryset.none()

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

class UserViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    owner_field = 'user_id'

    def get_permissions(self):
        if self.action == 'list':
            self.permission_classes = [permissions.IsAuthenticated] # Only authenticated users can list
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsOwnerOrAdmin)] # Only admin or owner can retrieve/update/delete
        elif self.action == 'create':
            self.permission_classes = [IsAdminUser | permissions.AllowAny] # Allow any user to create an account (handled by RegisterView)
        return super().get_permissions()

    def get_filtered_queryset(self, user, base_queryset):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            # For these actions, return the full queryset and let object-level permissions handle access
            return base_queryset
        # For 'list' action, filter by owner
        return super().get_filtered_queryset(user, base_queryset)

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

class TechnicianAvailabilityViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
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
        # Get the initial queryset from the ModelViewSet (skipping OwnerFilteredQuerysetMixin's get_queryset)
        base_queryset = super(OwnerFilteredQuerysetMixin, self).get_queryset()

        if user.is_authenticated and user.user_type.user_type_name == 'admin':
            return base_queryset
        elif user.is_authenticated:
            # Authenticated non-admin technicians can only see their own availability for all actions.
            # Clients can view all availability.
            if user.user_type.user_type_name == 'technician':
                return base_queryset.filter(technician_user=user)
            elif user.user_type.user_type_name == 'client':
                return base_queryset # Clients can view all availability
        else: # User is not authenticated
            # Check if any permission allows unauthenticated read access for list/retrieve actions
            has_read_only_permission = any(isinstance(perm, permissions.AllowAny) or isinstance(perm, IsAuthenticatedOrReadOnly) for perm in self.get_permissions())
            if has_read_only_permission and self.action in ['list', 'retrieve']:
                return base_queryset # Allow unauthenticated read access for list/retrieve
        return base_queryset.none()

class TechnicianSkillViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = TechnicianSkill.objects.all()
    serializer_class = TechnicianSkillSerializer
    owner_field = 'technician_user'

    def get_permissions(self):
        if self.action == 'create':
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

    def get_filtered_queryset(self, user, base_queryset):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            # For these actions, return the full queryset and let object-level permissions handle access
            return base_queryset
        elif self.action == 'list':
            if user.user_type.user_type_name == 'technician':
                return base_queryset.filter(technician_user=user)
            elif user.user_type.user_type_name == 'client':
                return base_queryset # Clients can see all skills
        return base_queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create skills.")

        if user.user_type.user_type_name == 'technician':
            serializer.save(technician_user=user)
        elif user.user_type.user_type_name == 'admin':
            if 'technician_user' not in self.request.data:
                raise serializers.ValidationError({"technician_user": "This field is required for admin users."})
            serializer.save()
        else:
            raise PermissionDenied("Only technicians and admins can create skills.")

class VerificationDocumentViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = VerificationDocument.objects.all()
    serializer_class = VerificationDocumentSerializer
    owner_field = 'technician_user'

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAdminUser | IsTechnicianUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
        else: # list, retrieve
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
        return super().get_permissions()

    def get_filtered_queryset(self, user, base_queryset):
        if user.user_type.user_type_name == 'technician':
            return base_queryset.filter(technician_user=user)
        return base_queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create verification documents.")

        if user.user_type.user_type_name == 'technician':
            requested_technician_user_id = self.request.data.get('technician_user')
            if requested_technician_user_id and requested_technician_user_id != user.user_id:
                raise PermissionDenied("Technicians can only create verification documents for themselves.")
            serializer.save(technician_user=user)
        elif user.user_type.user_type_name == 'admin':
            if 'technician_user' not in self.request.data:
                raise serializers.ValidationError({"technician_user": "This field is required for admin users."})
            serializer.save()
        else:
            raise PermissionDenied("Only technicians and admins can create verification documents.")

class OrderViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser | (IsClientUser & IsClientOwnerOrAdmin) | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
    owner_field = 'client_user' # Default owner field for filtering

    def get_queryset(self):
        user = self.request.user
        # Get the initial queryset from the ModelViewSet (skipping OwnerFilteredQuerysetMixin's get_queryset)
        base_queryset = super(OwnerFilteredQuerysetMixin, self).get_queryset()

        if user.is_authenticated and user.user_type.user_type_name == 'admin':
            return base_queryset
        elif user.is_authenticated:
            # Authenticated non-admin users get filtered for all actions (list, retrieve, update, destroy)
            # If an object is not in their filtered queryset, it will result in a 404.
            # Object-level permissions will then handle specific action permissions (e.g., 403 if found but no update permission).
            if user.user_type.user_type_name == 'client':
                return base_queryset.filter(client_user=user)
            elif user.user_type.user_type_name == 'technician':
                return base_queryset.filter(technician_user=user)
        return base_queryset.none()

class ProjectOfferViewset(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
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

    def get_filtered_queryset(self, user, base_queryset):
        if user.user_type.user_type_name == 'technician':
            if self.action == 'list':
                return base_queryset.filter(technician_user=user)
            return base_queryset # For detail actions, rely on object-level permissions
        elif user.user_type.user_type_name == 'client':
            if self.action == 'list':
                return base_queryset.filter(order__client_user=user)
            return base_queryset # For detail actions, rely on object-level permissions
        return base_queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create project offers.")

        if user.user_type.user_type_name == 'technician':
            requested_technician_user_id = self.request.data.get('technician_user')
            if requested_technician_user_id and requested_technician_user_id != user.user_id:
                raise PermissionDenied("Technicians can only create offers for themselves.")
            serializer.save(technician_user=user)
        elif user.user_type.user_type_name == 'admin':
            if 'technician_user' not in self.request.data:
                raise serializers.ValidationError({"technician_user": "This field is required for admin users."})
            serializer.save()
        else:
            raise PermissionDenied("Only technicians and admins can create project offers.")

class AddressViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAdminUser | (IsClientUser & IsUserOwnerOrAdmin)]
    owner_field = 'user'

    def get_filtered_queryset(self, user, base_queryset):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            # For these actions, return the full queryset and let object-level permissions handle access
            return base_queryset
        # For 'list' action, filter by owner
        return super().get_filtered_queryset(user, base_queryset)

class PaymentMethodViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAdminUser | ((IsClientUser | IsTechnicianUser) & IsUserOwnerOrAdmin)]
    owner_field = 'user'

    def get_queryset(self):
        user = self.request.user
        base_queryset = super().get_queryset()

        if user.is_authenticated and user.user_type.user_type_name == 'admin':
            return base_queryset
        elif user.is_authenticated and user.user_type.user_type_name in ['client', 'technician']:
            return base_queryset.filter(user=user)
        return base_queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create payment methods.")

        if user.user_type.user_type_name in ['client', 'technician']:
            if 'user' in self.request.data and self.request.data['user'] != user.user_id:
                raise PermissionDenied("Users can only create payment methods for themselves.")
            serializer.save(user=user)
        elif user.user_type.user_type_name == 'admin':
            if 'user' not in self.request.data:
                raise serializers.ValidationError({"user": "This field is required for admin users."})
            serializer.save()
        else:
            raise PermissionDenied("Only clients, technicians, and admins can create payment methods.")

class NotificationPreferenceViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = NotificationPreference.objects.all()
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAdminUser | (IsClientUser & IsUserOwnerOrAdmin)]
    owner_field = 'user'

    def get_filtered_queryset(self, user, base_queryset):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            # For these actions, return the full queryset and let object-level permissions handle access
            return base_queryset
        # For 'list' action, filter by owner
        if user.user_type.user_type_name == 'client':
            return base_queryset.filter(user=user)
        return base_queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create notification preferences.")

        if user.user_type.user_type_name == 'client':
            if 'user' in self.request.data and self.request.data['user'] != user.user_id:
                raise PermissionDenied("Clients can only create notification preferences for themselves.")
            serializer.save(user=user)
        elif user.user_type.user_type_name == 'admin':
            if 'user' not in self.request.data:
                raise serializers.ValidationError({"user": "This field is required for admin users."})
            serializer.save()
        else:
            raise PermissionDenied("Only clients and admins can create notification preferences.")

class NotificationViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsUserOwnerOrAdmin)]
    owner_field = 'user'

    def get_queryset(self):
        user = self.request.user
        base_queryset = super().get_queryset() # Get the initial queryset from the next class in MRO (e.g., ModelViewSet)

        if user.is_authenticated and user.user_type.user_type_name == 'admin':
            return base_queryset # Admin sees all
        elif user.is_authenticated:
            # Authenticated non-admin users get filtered for all actions (list, retrieve, update, destroy)
            # If an object is not in their filtered queryset, it will result in a 404.
            # Object-level permissions will then handle specific action permissions (e.g., 403 if found but no update permission).
            return base_queryset.filter(user=user)
        else: # User is not authenticated
            # Notifications are not publicly accessible
            return base_queryset.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create reviews.")

        if user.user_type.user_type_name == 'client':
            requested_client_user_id = self.request.data.get('reviewer')
            if requested_client_user_id and requested_client_user_id != user.user_id:
                raise PermissionDenied("Clients can only create reviews for themselves.")
            serializer.save(reviewer=user)
        elif user.user_type.user_type_name == 'technician':
            requested_reviewer_id = self.request.data.get('reviewer')
            if requested_reviewer_id and requested_reviewer_id != user.user_id:
                raise PermissionDenied("Technicians can only create reviews for themselves (as a client).")
            if 'technician' not in self.request.data or 'order' not in self.request.data:
                raise serializers.ValidationError({"detail": "Technician and order fields are required when a technician creates a review."})
            serializer.save(reviewer=user)
        elif user.user_type.user_type_name == 'admin':
            if 'reviewer' not in self.request.data or 'technician' not in self.request.data:
                raise serializers.ValidationError({"detail": "Reviewer and technician fields are required for admin users."})
            serializer.save()
        else:
            raise PermissionDenied("Only clients, technicians, and admins can create reviews.")
class IssueReportViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = IssueReport.objects.all()
    serializer_class = IssueReportSerializer
    permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsUserOwnerOrAdmin)]
    owner_field = 'reporter'

    def get_filtered_queryset(self, user, base_queryset):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            # For these actions, return the full queryset and let object-level permissions handle access
            return base_queryset
        # For 'list' action, filter by owner
        return super().get_filtered_queryset(user, base_queryset)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create issue reports.")
        serializer.save(reporter=user)

class TransactionViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    owner_field = 'user'

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsUserOwnerOrAdmin)]
        else: # list, retrieve
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsUserOwnerOrAdmin)]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ConversationViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsConversationParticipantOrAdmin)]

    def get_filtered_queryset(self, user, base_queryset):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return base_queryset # Rely on object-level permissions
        return base_queryset.filter(participants=user)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create conversations.")
        
        participants_data = self.request.data.get('participants')
        if user.user_type.user_type_name != 'admin':
            if not participants_data or user.user_id not in participants_data:
                raise serializers.ValidationError({"participants": "The authenticated user must be a participant in the conversation."})
        
        serializer.save()

class MessageViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsMessageSenderOrAdmin)]
        else: # list, retrieve, create
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsConversationParticipantOrAdmin)]
        return super().get_permissions()

    def get_filtered_queryset(self, user, base_queryset):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return base_queryset # Rely on object-level permissions
        return base_queryset.filter(conversation__participants=user)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create messages.")
        
        conversation_id = self.request.data.get('conversation')
        if not conversation_id:
            raise serializers.ValidationError({"conversation": "This field is required."})
        
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            raise serializers.ValidationError({"conversation": "Conversation does not exist."})
        
        if user.user_type.user_type_name != 'admin' and user not in conversation.participants.all():
            raise PermissionDenied("You are not a participant in this conversation.")
        
        serializer.save(sender=user, conversation=conversation)
