from rest_framework import viewsets, permissions, serializers
from .models import Order, ProjectOffer
from rest_framework.exceptions import PermissionDenied
from .serializers import OrderSerializer, ProjectOfferSerializer
from api.permissions import IsAdminUser, IsClientUser, IsTechnicianUser, IsClientOwnerOrAdmin, IsTechnicianOwnerOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin # This import is no longer needed, but keeping for now to avoid breaking other apps that might use it.

class OrderViewSet(viewsets.ModelViewSet):
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

class ProjectOfferViewset(viewsets.ModelViewSet):
    queryset = ProjectOffer.objects.all()
    serializer_class = ProjectOfferSerializer
    lookup_field = 'offer_id'

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAdminUser | IsTechnicianUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
        else: # list, retrieve
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin) | (IsClientUser & IsClientOwnerOrAdmin)]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.user_type.user_type_name == 'admin':
            return ProjectOffer.objects.all()
        elif user.is_authenticated and user.user_type.user_type_name == 'technician':
            return ProjectOffer.objects.filter(technician_user=user)
        elif user.is_authenticated and user.user_type.user_type_name == 'client':
            return ProjectOffer.objects.filter(order__client_user=user)
        return ProjectOffer.objects.all() # Return all for unauthenticated, let permissions handle 401/403

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
