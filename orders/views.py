from rest_framework import viewsets, permissions, serializers
from .models import Order, ProjectOffer
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from .serializers import OrderSerializer, ProjectOfferSerializer
from api.permissions import IsAdminUser, IsClientUser, IsTechnicianUser, IsClientOwnerOrAdmin, IsTechnicianOwnerOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin

class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

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
    pagination_class = OrderPagination
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    lookup_field = 'order_id'

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'list':
            # For list, only allow clients and admins. Technicians should not see generic order list
            self.permission_classes = [IsAdminUser | IsClientUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | IsClientOwnerOrAdmin | IsTechnicianOwnerOrAdmin]
        else: # retrieve
            self.permission_classes = [IsAdminUser | IsClientUser | IsTechnicianUser]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none() # No orders for unauthenticated users

        if user.user_type.user_type_name == 'admin':
            return Order.objects.all()
        elif user.user_type.user_type_name == 'client':
            return Order.objects.filter(client_user=user)
        elif user.user_type.user_type_name == 'technician':
            # Technicians can only see orders they're assigned to, not a generic list
            # For list action, return empty queryset to enforce permission restrictions
            if self.action == 'list':
                return Order.objects.none()
            return Order.objects.filter(technician_user=user)
        return Order.objects.none() # Should not be reached if user_type is handled

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

class WorkerTasksViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows technicians to view their assigned tasks (orders).

    list:
    Return a list of orders assigned to the authenticated technician.
    Supports filtering by order_status using order_status__in parameter (e.g., ?order_status__in=pending,in_progress)
    Supports limiting results using limit parameter (e.g., ?limit=3)
    Permissions: Authenticated Technician User only.
    Usage: GET /api/orders/worker-tasks/
    Usage: GET /api/orders/worker-tasks/?order_status__in=pending,in_progress&limit=3

    retrieve:
    Return a specific order assigned to the authenticated technician.
    Permissions: Authenticated Technician User only.
    Usage: GET /api/orders/worker-tasks/{order_id}/
    """
    serializer_class = OrderSerializer
    lookup_field = 'order_id'

    def get_permissions(self):
        self.permission_classes = [IsTechnicianUser]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none()

        # Only technicians can access this endpoint
        if user.user_type.user_type_name != 'technician':
            return Order.objects.none()

        # Start with orders assigned to this technician
        queryset = Order.objects.filter(technician_user=user)

        # Apply status filtering if provided (use order_status, not status)
        status_filter = self.request.query_params.get('status__in')
        if status_filter:
            status_list = [status.strip() for status in status_filter.split(',')]
            queryset = queryset.filter(order_status__in=status_list)
        
        # Also support order_status__in parameter
        order_status_filter = self.request.query_params.get('order_status__in')
        if order_status_filter:
            status_list = [status.strip() for status in order_status_filter.split(',')]
            queryset = queryset.filter(order_status__in=status_list)

        # Apply limit if provided - must do this before ordering
        limit = self.request.query_params.get('limit')
        if limit and limit.isdigit():
            queryset = queryset.order_by('-creation_timestamp')[:int(limit)]
        else:
            # Always order by creation date, most recent first
            queryset = queryset.order_by('-creation_timestamp')

        return queryset
