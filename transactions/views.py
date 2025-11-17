from rest_framework import viewsets, permissions
from .models import Transaction
from .serializers import TransactionSerializer
from api.permissions import IsAdminUser, IsUserOwnerOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin

class TransactionViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Transactions to be viewed or edited.

    list:
    Return a list of transactions for the authenticated user. Admins see all.
    Permissions: Authenticated User (owner) or Admin User.
    Usage: GET /api/transactions/

    retrieve:
    Return a specific transaction by ID.
    Permissions: Authenticated User (owner) or Admin User.
    Usage: GET /api/transactions/{id}/

    create:
    Create a new transaction. The authenticated user will be set as the user for the transaction.
    Permissions: Authenticated User (owner) or Admin User.
    Usage: POST /api/transactions/
    Body: {"order": 1, "amount": 100.00, "transaction_type": "Payment", "status": "Completed"}

    update:
    Update an existing transaction.
    Permissions: Authenticated User (owner) or Admin User.
    Usage: PUT /api/transactions/{id}/
    Body: {"status": "Refunded"}

    partial_update:
    Partially update an existing transaction.
    Permissions: Authenticated User (owner) or Admin User.
    Usage: PATCH /api/transactions/{id}/
    Body: {"amount": 90.00}

    destroy:
    Delete a transaction.
    Permissions: Authenticated User (owner) or Admin User.
    Usage: DELETE /api/transactions/{id}/
    """
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
