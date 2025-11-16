from rest_framework import viewsets, permissions
from ..models.transactions import Transaction
from ..serializers import TransactionSerializer
from ..permissions import IsAdminUser, IsUserOwnerOrAdmin
from ..mixins import OwnerFilteredQuerysetMixin

class TransactionViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    owner_field = 'user'

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsUserOwnerOrAdmin)]
        else: # list, retrieve
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsUserOwnerOrAdmin)]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
