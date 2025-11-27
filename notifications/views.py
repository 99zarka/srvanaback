from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from .models import NotificationPreference, Notification
from .serializers import NotificationPreferenceSerializer, NotificationSerializer
from api.permissions import IsAdminUser, IsClientUser, IsUserOwnerOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin

class NotificationPreferenceViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Notification Preferences to be viewed or edited.

    list:
    Return a list of notification preferences for the authenticated user.
    Permissions: Authenticated Client User (owner) or Admin User.
    Usage: GET /api/notifications/preferences/

    retrieve:
    Return a specific notification preference by ID.
    Permissions: Authenticated Client User (owner) or Admin User.
    Usage: GET /api/notifications/preferences/{id}/

    create:
    Create new notification preferences for the authenticated user.
    Permissions: Authenticated Client User or Admin User.
    Usage: POST /api/notifications/preferences/
    Body: {"user": 1, "email_notifications": true, "sms_notifications": false}

    update:
    Update existing notification preferences.
    Permissions: Authenticated Client User (owner) or Admin User.
    Usage: PUT /api/notifications/preferences/{id}/
    Body: {"email_notifications": false}

    partial_update:
    Partially update existing notification preferences.
    Permissions: Authenticated Client User (owner) or Admin User.
    Usage: PATCH /api/notifications/preferences/{id}/
    Body: {"sms_notifications": true}

    destroy:
    Delete notification preferences.
    Permissions: Authenticated Client User (owner) or Admin User.
    Usage: DELETE /api/notifications/preferences/{id}/
    """
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
    """
    API endpoint that allows Notifications to be viewed.

    list:
    Return a list of notifications for the authenticated user.
    Permissions: Authenticated User (owner) or Admin User.
    Usage: GET /api/notifications/

    retrieve:
    Return a specific notification by ID.
    Permissions: Authenticated User (owner) or Admin User.
    Usage: GET /api/notifications/{id}/

    create:
    Create a new notification. The authenticated user will be set as the recipient.
    Permissions: Authenticated User or Admin User.
    Usage: POST /api/notifications/
    Body: {"message": "Your order has been updated.", "notification_type": "order_update"}

    update:
    Update an existing notification.
    Permissions: Authenticated User (owner) or Admin User.
    Usage: PUT /api/notifications/{id}/
    Body: {"read": true}

    partial_update:
    Partially update an existing notification.
    Permissions: Authenticated User (owner) or Admin User.
    Usage: PATCH /api/notifications/{id}/
    Body: {"read": true}

    destroy:
    Delete a notification.
    Permissions: Authenticated User (owner) or Admin User.
    Usage: DELETE /api/notifications/{id}/
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsUserOwnerOrAdmin)]
    owner_field = 'user'

    def get_queryset(self):
        user = self.request.user
        base_queryset = super().get_queryset() # Get the initial queryset from the next class in MRO (e.g., ModelViewSet)

        if user.is_authenticated and user.user_type.user_type_name == 'admin':
            return base_queryset.filter(user=user) # Admin sees only their own notifications
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
