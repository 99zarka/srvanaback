from rest_framework import permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied
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
