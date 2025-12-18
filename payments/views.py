from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from django.db import transaction as db_transaction
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from users.models import User
from transactions.models import Transaction
from .models import Payment, PaymentMethod
from .serializers import PaymentMethodSerializer, PaymentSerializer
from api.permissions import IsAdminUser, IsClientUser, IsTechnicianUser, IsUserOwnerOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin
from srvana.paymob_utils import get_auth_token, register_order, get_payment_key, validate_hmac, pay_with_token

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
    """
    pagination_class = PaymentMethodPagination
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    owner_field = 'user'

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'list':
            self.permission_classes = [IsAdminUser | permissions.IsAuthenticated]
        else:
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsUserOwnerOrAdmin)]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        user = self.request.user
        base_queryset = super().get_queryset()

        if user.is_authenticated and user.user_type.user_type_name in ['client', 'technician', 'admin']:
            return base_queryset.filter(user=user)
        else:
            return base_queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create payment methods.")

        if user.user_type.user_type_name == 'admin':
            if 'user' in self.request.data:
                serializer.save()
            else:
                serializer.save(user=user)
        else:
            serializer.save(user=user)

class PaymentViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Payments to be viewed or edited.
    """
    pagination_class = PaymentPagination
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    owner_field = 'user'

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [IsAdminUser | ((IsClientUser | IsTechnicianUser) & IsUserOwnerOrAdmin)]
        elif self.action == 'webhook':
            # Webhook is public (Paymob calls it), security is handled via HMAC validation
            self.permission_classes = [permissions.AllowAny]
        else:
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
        """
        Initiates a deposit securely via Paymob.
        Returns the Iframe URL for the user to proceed with payment.
        Supports One-Click Payment via saved tokens.
        """
        amount = request.data.get('amount')
        payment_method_id = request.data.get('payment_method_id') # Optional: for Saved Card
        
        try:
            amount = float(amount)
            if amount <= 0:
                 raise ValueError
        except (ValueError, TypeError):
             raise ValidationError({'amount': 'Valid positive amount is required for deposit.'})
        
        user = request.user
        amount_decimal = Decimal(str(amount))
        amount_cents = int(amount_decimal * 100) # Paymob expects cents

        try:
            # 1. Authenticate with Paymob
            auth_token = get_auth_token()

            # 2. Create Pending Transaction internally
            # We create it first to get an ID for merchant_order_id
            transaction_obj = Transaction.objects.create(
                source_user=user,
                destination_user=user,
                transaction_type='DEPOSIT',
                amount=amount_decimal,
                currency='EGP',
                status='PENDING',
                transaction_id=None 
            )
            
            # 3. Register Order at Paymob
            merchant_order_id = f"TXN-{transaction_obj.id}"
            try:
                paymob_order_id = register_order(auth_token, amount_cents, merchant_order_id)
            except Exception as e:
                # If paymob order fails, delete local transaction to avoid zombies
                transaction_obj.delete()
                raise e

            # Save the Paymob Order ID 
            transaction_obj.external_id = str(paymob_order_id)
            transaction_obj.transaction_id = merchant_order_id
            transaction_obj.save(update_fields=['external_id', 'transaction_id'])

            # 4. Generate Payment Key
            billing_data = {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": user.phone_number
            }
            
            payment_key = get_payment_key(auth_token, paymob_order_id, billing_data, amount_cents)

            # 5. Handle Payment (Token vs New Card)
            if payment_method_id:
                # PAY WITH SAVED TOKEN
                try:
                    payment_method = PaymentMethod.objects.get(id=payment_method_id, user=user)
                    if not payment_method.paymob_token:
                        raise ValidationError("This payment method cannot be used for automatic payment.")
                    
                    pay_result = pay_with_token(payment_method.paymob_token, payment_key)
                    
                    # Check result
                    pending_val = pay_result.get('pending', False)
                    success_val = pay_result.get('success', False)
                    redirect_url = pay_result.get('redirect_url')
                    
                    is_pending = str(pending_val).lower() == 'true'
                    is_success = str(success_val).lower() == 'true'
                    
                    if is_success and not is_pending:
                         return Response({
                            'message': 'Payment successful.',
                            'transaction_id': transaction_obj.id,
                            'success': True
                        }, status=status.HTTP_200_OK)
                        
                    elif is_pending and redirect_url:
                        # 3D Secure Required
                         return Response({
                            'message': '3D Secure verification required.',
                            'iframe_url': redirect_url,
                            'transaction_id': transaction_obj.id
                        }, status=status.HTTP_200_OK)
                    else:
                         return Response({'detail': 'Payment failed or declined.'}, status=status.HTTP_400_BAD_REQUEST)

                except PaymentMethod.DoesNotExist:
                     raise ValidationError("Invalid payment method.")
            else:
                # NEW CARD / IFRAME FLOW
                iframe_id = settings.PAYMOB_IFRAME_ID
                if not iframe_id:
                    raise ValidationError({'detail': 'Configuration Error: PAYMOB_IFRAME_ID not set.'})
                    
                iframe_url = f"https://accept.paymob.com/api/acceptance/iframes/{iframe_id}?payment_token={payment_key}"

                return Response({
                    'message': 'Deposit initiated successfully. Please proceed to payment.',
                    'iframe_url': iframe_url,
                    'transaction_id': transaction_obj.id
                }, status=status.HTTP_200_OK)

        except ValidationError as e:
            raise e
        except Exception as e:
            # In case of API failure, we might want to mark transaction as failed or delete it.
            # logging.error(f"Paymob Error: {str(e)}")
            return Response({'detail': f"Payment Gateway Error: {str(e)}"}, status=status.HTTP_502_BAD_GATEWAY)

    @action(detail=False, methods=['post', 'get'], permission_classes=[permissions.AllowAny], authentication_classes=[], url_path='webhook')
    @method_decorator(csrf_exempt)
    def webhook(self, request):
        """
        Paymob Webhook Listener.
        Validates HMAC signature and updates User Balance upon successful payment.
        Captures Card Tokens for 'Saved Cards' feature.
        """
        print(f"DEBUG Webhook Payload: {request.data}")

        event_type = request.data.get('type')
        
        # We process TRANSACTION (Balance) and TOKEN (Save Card)
        if event_type and event_type not in ['TRANSACTION', 'TOKEN']:
             return Response(
                {'message': f'Ignored event type: {event_type}.'}, 
                status=status.HTTP_200_OK
            )

        # Merge Data for HMAC Validation
        data_source = request.data.get('obj', {}).copy()
        if not data_source:
            data_source = request.data.copy()
        data_source.update(request.GET.dict())

        # Validate HMAC
        hmac_secret = settings.PAYMOB_HMAC_SECRET
        if not validate_hmac(data_source, hmac_secret):
             return Response({'detail': 'Invalid HMAC Signature'}, status=status.HTTP_403_FORBIDDEN)

        # --- HANDLE TOKEN SAVE EVENT ---
        if event_type == 'TOKEN':
            # extracting token data
            # obj structure for TOKEN: {token: "...", masked_pan: "...", order_id: "...", card_subtype: "..." ...}
            token = data_source.get('token')
            masked_pan = data_source.get('masked_pan')
            card_subtype = data_source.get('card_subtype') # e.g. Visa
            email = data_source.get('email')
            paymob_order_id = data_source.get('order_id') # Order ID linked to this tokenization

            if not token or not paymob_order_id:
                 return Response({'detail': 'Invalid Token Data'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                with db_transaction.atomic():
                    # 1. Lookup User via Order ID
                    # We need to find the specific Transaction that created this Order
                    trans = Transaction.objects.filter(external_id=str(paymob_order_id)).first()
                    
                    if not trans:
                        # Fallback: Maybe order_id in transaction is stored differently?
                        # Or transaction failed before saving ID?
                        print(f"WARNING: Could not find transaction for Order ID {paymob_order_id} to save token.")
                        return Response({'detail': 'Transaction not found for token'}, status=status.HTTP_404_NOT_FOUND)
                    
                    user = trans.source_user

                    # 2. Save/Update Payment Method
                    # We use update_or_create to handle idempotency (if Paymob sends webhook multiple times)
                    # Unique constraint is (user, masked_pan, card_type)
                    pm, created = PaymentMethod.objects.update_or_create(
                        user=user,
                        masked_pan=masked_pan,
                        card_type=card_subtype,
                        defaults={
                            'paymob_token': token,
                            'expiration_date': data_source.get('expiry_year', '') + '/' + data_source.get('expiry_month', ''), # Might not be available
                            'email': email
                        }
                    )
                    action = "Created" if created else "Updated"
                    print(f"Token Saved: {action} payment method {masked_pan} for user {user.email}")
                    
                    return Response({'detail': 'Token saved successfully'}, status=status.HTTP_200_OK)

            except Exception as e:
                print(f"Error saving token: {str(e)}")
                return Response({'detail': f'Error saving token'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # --- HANDLE TRANSACTION EVENT ---
        # Logic remains similar but checked against 'success'
        is_success = data_source.get('success')
        if str(is_success).lower() != 'true':
            return Response({'detail': 'Transaction not successful'}, status=status.HTTP_200_OK)

        paymob_order_id = data_source.get('order')
        if isinstance(paymob_order_id, dict):
             paymob_order_id = paymob_order_id.get('id')
             
        merchant_order_id = data_source.get('merchant_order_id')
        
        if not paymob_order_id and not merchant_order_id:
             return Response({'detail': 'Missing Order ID'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with db_transaction.atomic():
                trans = Transaction.objects.select_for_update().filter(external_id=str(paymob_order_id)).first()
                if not trans and merchant_order_id:
                     try:
                         txn_id_internal = merchant_order_id.replace('TXN-', '')
                         trans = Transaction.objects.select_for_update().filter(id=txn_id_internal).first()
                     except:
                         pass

                if not trans:
                    return Response({'detail': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

                if trans.status == 'COMPLETED':
                    return Response({'detail': 'Transaction already processed'}, status=status.HTTP_200_OK)

                # Update Balance
                amount = trans.amount
                user = trans.source_user
                user.refresh_from_db()
                
                user.available_balance += amount
                user.save(update_fields=['available_balance'])
                
                trans.status = 'COMPLETED'
                trans.save(update_fields=['status'])

            return Response({'detail': 'Balance updated successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'detail': f'Processing Error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
                currency='EGP',
                status='COMPLETED', # Mark manual/mock withdrawal as completed for now
                payment_method=payment_method 
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
                currency='EGP',
                status='COMPLETED'
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
            if 'user' in self.request.data:
                serializer.save()
            else:
                serializer.save(user=user)
        else:
            serializer.save(user=user)
