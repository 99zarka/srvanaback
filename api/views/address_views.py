from rest_framework import viewsets, permissions
from ..models.addresses import Address
from ..serializers import AddressSerializer
from ..permissions import IsAdminUser, IsClientUser, IsUserOwnerOrAdmin
from ..mixins import OwnerFilteredQuerysetMixin

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
