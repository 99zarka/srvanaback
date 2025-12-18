from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q # Import Q for complex queries
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
    queryset = Transaction.objects.all().order_by('-timestamp')
    serializer_class = TransactionSerializer
    owner_field = 'source_user' # Updated to source_user

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsUserOwnerOrAdmin)]
        elif self.action == 'me':
            self.permission_classes = [permissions.IsAuthenticated]
        else: # list, retrieve
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsUserOwnerOrAdmin)]
        return super().get_permissions()

    def perform_create(self, serializer):
        if self.request.user.is_staff or self.request.user.is_superuser: # Check if admin
            # Admin can specify source_user and destination_user.
            # If source_user is not provided, default to admin user
            if 'source_user' not in serializer.validated_data:
                serializer.validated_data['source_user'] = self.request.user
            # If destination_user is not provided, default to source_user (which might be specified by admin or defaulted to admin)
            if 'destination_user' not in serializer.validated_data:
                serializer.validated_data['destination_user'] = serializer.validated_data['source_user']
        else:
            # Regular user: source_user is always the authenticated user
            serializer.validated_data['source_user'] = self.request.user
            # If destination_user is not provided, default to the authenticated user
            if 'destination_user' not in serializer.validated_data:
                serializer.validated_data['destination_user'] = self.request.user
        serializer.save()

    def get_filtered_queryset(self, user, base_queryset):
        """
        Returns the queryset for non-admin authenticated users,
        filtered by either source_user or destination_user using Q objects.
        """
        return base_queryset.filter(Q(source_user=user) | Q(destination_user=user)).order_by('-timestamp')

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Returns a list of transactions for the currently authenticated user,
        where the user is either the source or destination.
        """
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)
        
        queryset = self.get_filtered_queryset(request.user, self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
