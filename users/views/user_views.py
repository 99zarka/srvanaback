from rest_framework import viewsets, permissions
from users.models import User, UserType
from users.serializers import UserTypeSerializer, UserSerializer
from api.permissions import IsAdminUser, IsOwnerOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin

class UserTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows UserTypes to be viewed or edited.

    list:
    Return a list of all user types.
    Usage: GET /api/usertypes/

    retrieve:
    Return a specific user type by ID.
    Usage: GET /api/usertypes/{id}/

    create:
    Create a new user type. (Admin only)
    Usage: POST /api/usertypes/
    Body: {"name": "New User Type"}

    update:
    Update an existing user type. (Admin only)
    Usage: PUT /api/usertypes/{id}/
    Body: {"name": "Updated User Type"}

    partial_update:
    Partially update an existing user type. (Admin only)
    Usage: PATCH /api/usertypes/{id}/
    Body: {"name": "Partially Updated User Type"}

    destroy:
    Delete a user type. (Admin only)
    Usage: DELETE /api/usertypes/{id}/
    """
    queryset = UserType.objects.all()
    serializer_class = UserTypeSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        else: # list, retrieve
            self.permission_classes = [permissions.AllowAny] # Publicly accessible
        return super().get_permissions()

class UserViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Users to be viewed or edited.

    list:
    Return a list of all users. Requires authentication.
    Usage: GET /api/users/

    retrieve:
    Return a specific user by ID. Requires authentication and either admin privileges or ownership.
    Usage: GET /api/users/{id}/

    create:
    Create a new user. This is typically handled by a separate registration endpoint.
    Usage: POST /api/users/
    Body: {"username": "newuser", "email": "new@example.com", "password": "password123"}

    update:
    Update an existing user. Requires authentication and either admin privileges or ownership.
    Usage: PUT /api/users/{id}/
    Body: {"email": "updated@example.com"}

    partial_update:
    Partially update an existing user. Requires authentication and either admin privileges or ownership.
    Usage: PATCH /api/users/{id}/
    Body: {"username": "updatedusername"}

    destroy:
    Delete a user. Requires authentication and either admin privileges or ownership.
    Usage: DELETE /api/users/{id}/
    """
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
