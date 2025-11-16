from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from ..models.payment_methods import PaymentMethod
from ..serializers import PaymentMethodSerializer
from ..permissions import IsAdminUser, IsClientUser, IsTechnicianUser, IsUserOwnerOrAdmin
from ..mixins import OwnerFilteredQuerysetMixin

class PaymentMethodViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
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
