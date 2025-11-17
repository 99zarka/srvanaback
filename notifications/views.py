from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from .models import NotificationPreference, Notification
from .serializers import NotificationPreferenceSerializer, NotificationSerializer
from api.permissions import IsAdminUser, IsClientUser, IsUserOwnerOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin

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
