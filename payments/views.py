from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from django.db import transaction as db_transaction
from decimal import Decimal # Import Decimal
from users.models import User
from transactions.models import Transaction
from .models import Payment, PaymentMethod
from .serializers import PaymentMethodSerializer, PaymentSerializer
from api.permissions import IsAdminUser, IsClientUser, IsTechnicianUser, IsUserOwnerOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin
from .serializers import PaymentMethodSerializer, PaymentSerializer
from api.permissions import IsAdminUser, IsClientUser, IsTechnicianUser, IsUserOwnerOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin

class PaymentMethodPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class PaymentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

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
    Partially update an existing payment method. Technicians can be customers too.
    Permissions: Authenticated Client/Technician User (owner) or Admin User.
    Usage: PATCH /api/payments/methods/{id}/
    Body: {"expiration_date": "01/26"}

    destroy:
    Delete a payment method.
    Permissions: Authenticated Client/Technician User (owner) or Admin User.
    Usage: DELETE /api/payments/methods/{id}/
    """
    pagination_class = PaymentMethodPagination
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    owner_field = 'user'

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated] # Only require authentication for creation
        elif self.action == 'list':
            self.permission_classes = [IsAdminUser | permissions.IsAuthenticated] # Admins see all, authenticated see their own via get_queryset
        else: # retrieve, update, partial_update, destroy
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsUserOwnerOrAdmin)]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        user = self.request.user
        base_queryset = super().get_queryset()

        if user.is_authenticated and user.user_type.user_type_name in ['client', 'technician', 'admin']:
            return base_queryset.filter(user=user)
        else:
            return base_queryset.none() # Return none for unauthenticated, permissions will handle 401/403

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create payment methods.")

        if user.user_type.user_type_name == 'admin':
            # Admin can create for any user if 'user' is specified in data,
            # otherwise, if no 'user' is specified, assume admin is creating for themselves.
            if 'user' in self.request.data:
                serializer.save() # Admin creates for a specified user
            else:
                serializer.save(user=user) # Admin creates for themselves
        else:
            # Clients and technicians can only create payment methods for themselves.
            # The serializer's HiddenField(CurrentUserDefault()) ensures 'user' is the authenticated user.
            # We explicitly save with the authenticated user to enforce this for all non-admin roles.
            serializer.save(user=user)

class PaymentViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Payments to be viewed or edited.

    list:
    Return a list of payments for the authenticated user (client or technician) or all payments for admin.
    Permissions: Authenticated Client/Technician User (owner) or Admin User.
    Usage: GET /api/payments/

    retrieve:
    Return a specific payment by ID.
    Permissions: Authenticated Client/Technician User (owner) or Admin User.
    Usage: GET /api/payments/{id}/

    create:
    Create a new payment.
    Permissions: Authenticated Client/Technician User or Admin User.
    Usage: POST /api/payments/
    Body: {"order": 1, "user": 1, "amount": 100.00, "payment_method": 1, "transaction_id": "xyz123", "status": "COMPLETED"}

    update:
    Update an existing payment.
    Permissions: Authenticated Client/Technician User (owner) or Admin User.
    Usage: PUT /api/payments/{id}/
    Body: {"status": "REFUNDED"}

    partial_update:
    Partially update an existing payment. Technicians can be customers too.
    Permissions: Authenticated Client/Technician User (owner) or Admin User.
    Usage: PATCH /api/payments/{id}/
    Body: {"amount": 90.00}

    destroy:
    Delete a payment.
    Permissions: Authenticated Client/Technician User (owner) or Admin User.
    Usage: DELETE /api/payments/{id}/
    """
    pagination_class = PaymentPagination
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    owner_field = 'user'

    def get_permissions(self):
        if self.action == 'list':
            # Allow admin to see all, clients/technicians to see their own
            self.permission_classes = [IsAdminUser | ((IsClientUser | IsTechnicianUser) & IsUserOwnerOrAdmin)]
        else:
            # For other actions, admin or owners
            self.permission_classes = [IsAdminUser | ((IsClientUser | IsTechnicianUser) & IsUserOwnerOrAdmin)]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        base_queryset = super().get_queryset()

        if user.is_authenticated and user.user_type.user_type_name == 'admin':
            return base_queryset
        elif user.is_authenticated and user.user_type.user_type_name in ['client', 'technician']:
            return base_queryset.filter(user=user)
        return base_queryset.none()

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def deposit(self, request):
        amount = request.data.get('amount')
        payment_method_id = request.data.get('payment_method_id')

        if not amount or not isinstance(amount, (int, float)) or float(amount) <= 0:
            raise ValidationError({'amount': 'Valid positive amount is required for deposit.'})
        
        user = request.user
        amount = Decimal(str(amount)) # Ensure amount is Decimal

        try:
            payment_method = None
            if payment_method_id:
                # Use 'id' for primary key lookup
                payment_method = PaymentMethod.objects.get(id=payment_method_id, user=user) 
        except PaymentMethod.DoesNotExist:
            raise ValidationError({'payment_method_id': 'Payment method not found or does not belong to the user.'})

        with db_transaction.atomic():
            user.refresh_from_db() # Lock user row
            user.available_balance += amount
            user.save(update_fields=['available_balance'])

            Transaction.objects.create(
                source_user=user,
                destination_user=user,
                transaction_type='DEPOSIT',
                amount=amount,
                currency='USD',
                payment_method=payment_method # Pass the PaymentMethod object directly
            )
        return Response({
            'message': f"{amount} deposited successfully to available balance.",
            'user_id': user.user_id,
            'available_balance': user.available_balance,
            'in_escrow_balance': user.in_escrow_balance,
            'pending_balance': user.pending_balance,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def withdraw(self, request):
        amount = request.data.get('amount')
        payment_method_id = request.data.get('payment_method_id')

        if not amount or not isinstance(amount, (int, float)) or float(amount) <= 0:
            raise ValidationError({'amount': 'Valid positive amount is required for withdrawal.'})
        
        if not payment_method_id:
            raise ValidationError({'payment_method_id': 'Payment method is required for withdrawal.'})

        user = request.user
        amount = Decimal(str(amount)) # Ensure amount is Decimal

        try:
            # Use 'id' for primary key lookup
            payment_method = PaymentMethod.objects.get(id=payment_method_id, user=user) 
        except PaymentMethod.DoesNotExist:
            raise ValidationError({'payment_method_id': 'Payment method not found or does not belong to the user.'})

        with db_transaction.atomic():
            user.refresh_from_db() # Lock user row
            if user.available_balance < amount:
                raise ValidationError({'amount': 'Insufficient available balance for withdrawal.'})

            user.available_balance -= amount
            user.save(update_fields=['available_balance'])

            Transaction.objects.create(
                source_user=user,
                destination_user=user,
                transaction_type='WITHDRAWAL',
                amount=amount,
                currency='USD',
                payment_method=payment_method # Pass the PaymentMethod object directly
            )
        return Response({
            'message': f"{amount} withdrawn successfully from available balance.",
            'user_id': user.user_id,
            'available_balance': user.available_balance,
            'in_escrow_balance': user.in_escrow_balance,
            'pending_balance': user.pending_balance,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def transfer_pending_to_available(self, request):
        """
        Allows an authenticated user to transfer their entire pending_balance to available_balance.
        Permissions: Authenticated User.
        Usage: POST /api/payments/transfer-pending-to-available/
        """
        user = request.user

        with db_transaction.atomic():
            user.refresh_from_db() # Lock user row

            if user.pending_balance <= 0:
                raise ValidationError({'detail': 'No pending balance to transfer.'})

            amount_to_transfer = user.pending_balance

            # Move funds from pending_balance to available_balance
            user.pending_balance -= amount_to_transfer
            user.available_balance += amount_to_transfer
            user.save(update_fields=['pending_balance', 'available_balance'])

            # Create a transaction record for this internal transfer
            Transaction.objects.create(
                source_user=user,
                destination_user=user,
                transaction_type='PENDING_TO_AVAILABLE_TRANSFER',
                amount=amount_to_transfer,
                currency='USD',
            )

        return Response({
            'message': f"{amount_to_transfer} transferred from pending to available balance successfully.",
            'user_id': user.user_id,
            'available_balance': user.available_balance,
            'in_escrow_balance': user.in_escrow_balance,
            'pending_balance': user.pending_balance,
        }, status=status.HTTP_200_OK)


    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create payments.")

        if user.user_type.user_type_name == 'admin':
            # Admin can create for any user if 'user' is specified in data,
            # otherwise, if no 'user' is specified, assume admin is creating for themselves.
            if 'user' in self.request.data:
                serializer.save() # Admin creates for a specified user
            else:
                serializer.save(user=user) # Admin creates for themselves
        else:
            # Clients and technicians can only create payments for themselves.
            # The serializer (if using CurrentUserDefault) handles setting the user,
            # but we explicitly save with the authenticated user to enforce this.
            serializer.save(user=user)
