from rest_framework import viewsets, permissions
from users.models import User, UserType
from users.serializers import UserTypeSerializer, UserSerializer
from api.permissions import IsAdminUser, IsOwnerOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin

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
