from rest_framework import viewsets, permissions
from .models import Address
from .serializers import AddressSerializer
from api.permissions import IsAdminUser, IsClientUser, IsUserOwnerOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin

class AddressViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Addresses to be viewed or edited.

    list:
    Return a list of all addresses for the authenticated user.
    Permissions: Authenticated Client User (owner) or Admin User.
    Usage: GET /api/addresses/

    retrieve:
    Return a specific address by ID.
    Permissions: Authenticated Client User (owner) or Admin User.
    Usage: GET /api/addresses/{id}/

    create:
    Create a new address for the authenticated user.
    Permissions: Authenticated Client User (owner) or Admin User.
    Usage: POST /api/addresses/
    Body: {"street": "123 Main St", "city": "Anytown", "state": "CA", "zip_code": "12345", "country": "USA"}

    update:
    Update an existing address.
    Permissions: Authenticated Client User (owner) or Admin User.
    Usage: PUT /api/addresses/{id}/
    Body: {"street": "456 Oak Ave"}

    partial_update:
    Partially update an existing address.
    Permissions: Authenticated Client User (owner) or Admin User.
    Usage: PATCH /api/addresses/{id}/
    Body: {"city": "Newcity"}

    destroy:
    Delete an address.
    Permissions: Authenticated Client User (owner) or Admin User.
    Usage: DELETE /api/addresses/{id}/
    """
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
