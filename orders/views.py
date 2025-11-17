from rest_framework import viewsets, permissions, serializers
from .models import Order, ProjectOffer
from rest_framework.exceptions import PermissionDenied
from .serializers import OrderSerializer, ProjectOfferSerializer
from api.permissions import IsAdminUser, IsClientUser, IsTechnicianUser, IsClientOwnerOrAdmin, IsTechnicianOwnerOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin # This import is no longer needed, but keeping for now to avoid breaking other apps that might use it.

class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Orders to be viewed or edited.

    list:
    Return a list of orders for the authenticated user (client or technician) or all orders for admin.
    Permissions: Authenticated User (client/technician owner) or Admin User.
    Usage: GET /api/orders/

    retrieve:
    Return a specific order by ID.
    Permissions: Authenticated User (client/technician owner) or Admin User.
    Usage: GET /api/orders/{order_id}/

    create:
    Create a new order.
    Permissions: Authenticated User.
    Usage: POST /api/orders/
    Body: {"service": 1, "client_user": 1, "description": "Fix leaky faucet", "scheduled_date": "2025-12-01T10:00:00Z"}

    update:
    Update an existing order.
    Permissions: Authenticated User (client/technician owner) or Admin User.
    Usage: PUT /api/orders/{order_id}/
    Body: {"status": "Completed"}

    partial_update:
    Partially update an existing order.
    Permissions: Authenticated User (client/technician owner) or Admin User.
    Usage: PATCH /api/orders/{order_id}/
    Body: {"description": "Fixed and tested."}

    destroy:
    Delete an order.
    Permissions: Authenticated User (client/technician owner) or Admin User.
    Usage: DELETE /api/orders/{order_id}/
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    lookup_field = 'order_id'

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | IsClientOwnerOrAdmin | IsTechnicianOwnerOrAdmin]
        else: # list, retrieve
            self.permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.user_type.user_type_name == 'admin':
            return Order.objects.all()
        elif user.is_authenticated and user.user_type.user_type_name == 'client':
            return Order.objects.filter(client_user=user)
        elif user.is_authenticated and user.user_type.user_type_name == 'technician':
            return Order.objects.filter(technician_user=user)
        return Order.objects.all() # Return all for unauthenticated, let permissions handle 401/403

class ProjectOfferViewset(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Project Offers to be viewed or edited.

    list:
    Return a list of project offers. Technicians see their own offers, clients see offers for their orders, admins see all.
    Permissions: Authenticated User (technician owner, client owner) or Admin User.
    Usage: GET /api/orders/project_offers/

    retrieve:
    Return a specific project offer by ID.
    Permissions: Authenticated User (technician owner, client owner) or Admin User.
    Usage: GET /api/orders/project_offers/{offer_id}/

    create:
    Create a new project offer. Technicians can only create offers for themselves.
    Permissions: Authenticated Technician User or Admin User.
    Usage: POST /api/orders/project_offers/
    Body: {"order": 1, "technician_user": 2, "price": 150.00, "description": "Offer to fix faucet."}

    update:
    Update an existing project offer. Technicians can only update their own offers.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: PUT /api/orders/project_offers/{offer_id}/
    Body: {"price": 175.00}

    partial_update:
    Partially update an existing project offer. Technicians can only update their own offers.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: PATCH /api/orders/project_offers/{offer_id}/
    Body: {"description": "Revised offer details."}

    destroy:
    Delete a project offer. Technicians can only delete their own offers.
    Permissions: Authenticated Technician User (owner) or Admin User.
    Usage: DELETE /api/orders/project_offers/{offer_id}/
    """
    queryset = ProjectOffer.objects.all()
    serializer_class = ProjectOfferSerializer
    lookup_field = 'offer_id'
    owner_field = 'technician_user'

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
