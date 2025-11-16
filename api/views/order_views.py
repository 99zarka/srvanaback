from rest_framework import viewsets, permissions, serializers
from ..models.orders.core import Order
from ..models.orders.feedback import ProjectOffer
from rest_framework.exceptions import PermissionDenied
from ..serializers import OrderSerializer, ProjectOfferSerializer
from ..permissions import IsAdminUser, IsClientUser, IsTechnicianUser, IsClientOwnerOrAdmin, IsTechnicianOwnerOrAdmin
from ..mixins import OwnerFilteredQuerysetMixin

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
