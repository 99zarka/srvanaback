from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from .models import PaymentMethod
from .serializers import PaymentMethodSerializer
from api.permissions import IsAdminUser, IsClientUser, IsTechnicianUser, IsUserOwnerOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin

class PaymentMethodViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Payment Methods to be viewed or edited.

    list:
    Return a list of payment methods for the authenticated user.
    Permissions: Authenticated Client/Technician User (owner) or Admin User.
    Usage: GET /api/payments/methods/

    retrieve:
    Return a specific payment method by ID.
    Permissions: Authenticated Client/Technician User (owner) or Admin User.
    Usage: GET /api/payments/methods/{id}/

    create:
    Create a new payment method for the authenticated user.
    Permissions: Authenticated Client/Technician User or Admin User.
    Usage: POST /api/payments/methods/
    Body: {"user": 1, "card_number": "xxxx-xxxx-xxxx-1234", "card_type": "Visa", "expiration_date": "12/25"}

    update:
    Update an existing payment method.
    Permissions: Authenticated Client/Technician User (owner) or Admin User.
    Usage: PUT /api/payments/methods/{id}/
    Body: {"card_type": "MasterCard"}

    partial_update:
    Partially update an existing payment method.
    Permissions: Authenticated Client/Technician User (owner) or Admin User.
    Usage: PATCH /api/payments/methods/{id}/
    Body: {"expiration_date": "01/26"}

    destroy:
    Delete a payment method.
    Permissions: Authenticated Client/Technician User (owner) or Admin User.
    Usage: DELETE /api/payments/methods/{id}/
    """
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAdminUser | ((IsClientUser | IsTechnicianUser) & IsUserOwnerOrAdmin)]
    owner_field = 'user'

    def get_queryset(self):
        user = self.request.user
        base_queryset = super().get_queryset()

        if user.is_authenticated and user.user_type.user_type_name == 'admin':
            return base_queryset
        elif user.is_authenticated and user.user_type.user_type_name in ['client', 'technician']:
            return base_queryset.filter(user=user)
        return base_queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create payment methods.")

        if user.user_type.user_type_name in ['client', 'technician']:
            if 'user' in self.request.data and self.request.data['user'] != user.user_id:
                raise PermissionDenied("Users can only create payment methods for themselves.")
            serializer.save(user=user)
        elif user.user_type.user_type_name == 'admin':
            if 'user' not in self.request.data:
                raise serializers.ValidationError({"user": "This field is required for admin users."})
            serializer.save()
        else:
            raise PermissionDenied("Only clients, technicians, and admins can create payment methods.")
