from rest_framework import viewsets, permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction as db_transaction # Import for atomic operations
from django.db import models
from .models import Order, ProjectOffer
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from rest_framework.pagination import PageNumberPagination
from .serializers import OrderSerializer, ProjectOfferSerializer, ProjectOfferDetailSerializer, PublicOrderSerializer, ProjectOfferWithOrderSerializer
from api.permissions import IsAdminUser, IsClientUser, IsTechnicianUser, IsClientOwnerOrAdmin, IsTechnicianOwnerOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin
from notifications.models import Notification # Keep this for now, will replace usage with utils
from notifications.utils import create_notification # Import the helper function
from notifications.arabic_translations import ARABIC_NOTIFICATIONS
from users.models import User # Needed for notifying all technicians and for balance updates
from transactions.models import Transaction # Import Transaction model for escrow operations
from disputes.models import Dispute # Import Dispute model
from datetime import date, datetime, timedelta # Import datetime and timedelta for auto-release
from decimal import Decimal # Import Decimal

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
    Body: {"service": 1, "description": "Fix leaky faucet", "scheduled_date": "2025-12-01T10:00:00Z"}

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

    available_for_offer:
    Return a list of orders available for technician offers (orders without assigned technician).
    Permissions: Authenticated Technician User.
    Usage: GET /api/orders/available-for-offer/

    offers:
    Return a list of project offers for a specific order.
    Permissions: Authenticated Client User (owner of order) or Admin User.
    Usage: GET /api/orders/{order_id}/offers/

    accept_offer:
    Accept a specific project offer for an order.
    Permissions: Authenticated Client User (owner of order) or Admin User.
    Usage: POST /api/orders/{order_id}/accept-offer/{offer_id}/
    """
    pagination_class = OrderPagination
    # Optimized queryset for common relations
    queryset = Order.objects.select_related(
        'client_user', 
        'client_user__user_type',
        'technician_user', 
        'technician_user__user_type',
        'service'
    ).annotate(
        review_rating=models.F('review__rating'),
        review_comment=models.F('review__comment')
    ).prefetch_related(
        'project_offers',
        'project_offers__technician_user',
        'project_offers__technician_user__user_type',
        'disputes'
        # Remove 'review' from prefetch_related as we're using annotations
    ).order_by('-order_id')
    serializer_class = OrderSerializer
    lookup_field = 'order_id'

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated] # Allow any authenticated user to create
        elif self.action == 'list':
            # For list, only allow clients and admins. Technicians should not see generic order list
            self.permission_classes = [permissions.IsAuthenticated, IsAdminUser | IsClientOwnerOrAdmin | IsTechnicianOwnerOrAdmin]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsAdminUser | IsClientOwnerOrAdmin | IsTechnicianOwnerOrAdmin]
        elif self.action == 'available_for_offer':
            # Changed to AllowAny for public access
            self.permission_classes = [permissions.AllowAny] 
        elif self.action == 'public_detail':
            self.permission_classes = [permissions.AllowAny]
        elif self.action in ['accept_offer', 'decline_offer', 'release_funds', 'cancel_order']:
            # Actions primarily for the client owner or admin
            self.permission_classes = [IsAdminUser | IsClientOwnerOrAdmin]
        elif self.action == 'initiate_dispute':
            # Allow client owner or assigned technician or admin to initiate dispute
            self.permission_classes = [IsAdminUser | IsClientOwnerOrAdmin | IsTechnicianOwnerOrAdmin]
        elif self.action == 'offers':
            # Offers can be viewed by client owner, assigned technician, or admin
            self.permission_classes = [IsAdminUser | IsClientOwnerOrAdmin | IsTechnicianOwnerOrAdmin]
        elif self.action == 'mark_job_done' or self.action == 'start_job': # Added start_job
            # Action strictly for the assigned technician or admin
            self.permission_classes = [IsAdminUser | IsTechnicianOwnerOrAdmin]
        elif self.action == 'retrieve': # Explicitly handle retrieve
             self.permission_classes = [permissions.IsAuthenticated, IsAdminUser | IsClientOwnerOrAdmin | IsTechnicianOwnerOrAdmin]
        else: # Fallback for any other action
            self.permission_classes = [permissions.IsAuthenticated, IsAdminUser | IsClientUser | IsTechnicianUser]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        user = self.request.user
        base_queryset = Order.objects.select_related(
            'client_user', 
            'client_user__user_type',
            'technician_user', 
            'technician_user__user_type',
            'service'
        ).annotate(
            review_rating=models.F('review__rating'),
            review_comment=models.F('review__comment')
        ).prefetch_related(
            'project_offers',
            'project_offers__technician_user',
            'project_offers__technician_user__user_type',
            'disputes'
            # Remove 'review' from prefetch_related as we're using annotations
        ).order_by('-order_id')

        # For 'available_for_offer' and 'public_detail' actions, always filter for OPEN orders with no assigned technician
        if self.action in ['available_for_offer', 'public_detail']:
            return base_queryset.filter(technician_user__isnull=True, order_status='OPEN')


        # For detail views (retrieve, update, destroy, and custom actions like accept_offer, mark_job_done, etc.)
        # always return the full queryset. Permissions will then handle whether the user can actually access/modify it.
        if self.detail or self.action in ['accept_offer', 'decline_offer', 'mark_job_done', 'release_funds', 'initiate_dispute', 'cancel_order', 'offers', 'start_job']: # Added start_job
            return base_queryset

        # For list actions, apply specific filtering based on user role
        if not user.is_authenticated:
            return Order.objects.none() # Unauthenticated users see no orders in generic list, handled above for 'available_for_offer'

        # Check if we want orders with disputes only
        has_dispute = self.request.query_params.get('has_dispute')
        if has_dispute and has_dispute.lower() == 'true':
            base_queryset = base_queryset.filter(disputes__isnull=False).distinct()

        # Add order_status filter
        order_status = self.request.query_params.get('order_status')
        if order_status:
            base_queryset = base_queryset.filter(order_status=order_status)
            
        return_all = self.request.query_params.get('return_all') or ""
        if user.user_type.user_type_name == 'admin' and return_all.lower() == 'true':
            return base_queryset
        elif user.user_type.user_type_name in ['client' , 'technician', 'admin'] :
            return base_queryset.filter(client_user=user)


        return Order.objects.none() # Default fallback, should not be reached with proper user type handling

    def perform_create(self, serializer):
        """Automatically set client_user to the authenticated user on create."""
        user = self.request.user
        
        # Create the order with the client_user set to the authenticated user
        order = serializer.save(client_user=user)
        
        # 1. Notify client (confirmation)
        with db_transaction.atomic():
            create_notification(
                user=user,
                notification_type='order_created',
                title=ARABIC_NOTIFICATIONS['order_created_title'],
                message=ARABIC_NOTIFICATIONS['order_created_message'].format(order_id=order.order_id),
                related_order=order
            )
        
        # 2. Notify all technicians (new project available) - can be refined later
        technicians = User.objects.filter(user_type__user_type_name='technician')
        for tech_user in technicians:
            create_notification(
                user=tech_user,
                notification_type='new_project_available',
                title=ARABIC_NOTIFICATIONS['new_project_available_title'],
                message=ARABIC_NOTIFICATIONS['new_project_available_message'].format(order_id=order.order_id),
                related_order=order
            )

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def available_for_offer(self, request):
        """
        Return orders that are available for technician offers.
        These are orders without an assigned technician and with status 'OPEN'.
        """
        user = request.user
        # The permission_classes now allow any user, but the filtering below ensures only
        # relevant orders are shown. If the user is authenticated as a technician,
        # they still see the same list as intended previously.
        # Removed explicit PermissionDenied check for technicians as AllowAny handles it.

        # Get orders without assigned technician and in OPEN status
        available_orders = Order.objects.filter(
            technician_user__isnull=True,
            order_status='OPEN'
        ).select_related(
            'client_user', 
            'client_user__user_type',
            'service'
        ).prefetch_related(
            'project_offers',
            'project_offers__technician_user',
            'project_offers__technician_user__user_type'
        ).order_by('-creation_timestamp') # Keep original sorting for this specific action

        # Apply pagination
        page = self.paginate_queryset(available_orders)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(available_orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def public_detail(self, request, order_id=None):
        """
        Return details for a single public order (OPEN, no assigned technician).
        Accessible by any user (authenticated or unauthenticated).
        """
        try:
            # Get the object and then apply additional filters to ensure it's public
            order = self.get_object()
            if order.technician_user is not None or order.order_status != 'OPEN':
                raise NotFound("Project not found or not publicly available.")
        except Order.DoesNotExist:
            raise NotFound("Project not found.")

        # Serialize the order with public details
        order_serializer = PublicOrderSerializer(order)

        # Get and serialize the project offers for this order
        project_offers = ProjectOffer.objects.filter(order=order).select_related(
            'technician_user',
            'technician_user__user_type'
        ).order_by('-offer_date', '-offer_id')

        offers_serializer = ProjectOfferDetailSerializer(project_offers, many=True, context={'request': request})

        # Return both order details and offers
        return Response({
            'order': order_serializer.data,
            'project_offers': offers_serializer.data
        })

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def offers(self, request, order_id=None):
        """
        Return all project offers for a specific order.
        Only accessible by the client who owns the order, assigned technician, or admin.
        """
        try:
            order = self.get_object() 
        except Order.DoesNotExist:
            raise NotFound("Order not found.")

        # Check if user owns this order, is the assigned technician, or is admin
        if not (order.client_user == request.user or \
                (order.technician_user == request.user and request.user.user_type.user_type_name == 'technician') or \
                request.user.user_type.user_type_name == 'admin'):
            raise PermissionDenied("You can only view offers for your own orders or assigned tasks.")

        offers = ProjectOffer.objects.filter(order=order).select_related(
            'technician_user', 
            'technician_user__user_type'
        ).order_by('-offer_date', '-offer_id')
        
        # Apply pagination
        page = self.paginate_queryset(offers)
        if page is not None:
            serializer = ProjectOfferSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ProjectOfferSerializer(offers, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsClientOwnerOrAdmin])
    def accept_offer(self, request, order_id=None, offer_id=None):
        """
        Accept a specific project offer for an order.
        This will assign the technician to the order and update offer statuses.
        """
        try:
            order = self.get_object() 
        except Order.DoesNotExist:
            raise NotFound("Order not found.")

        # Check if user owns this order or is admin (already handled by permission_classes)

        # Ensure the order is in a state where an offer can be accepted
        if order.order_status not in ['OPEN', 'AWAITING_CLIENT_ESCROW_CONFIRMATION']: # Ensure status is uppercase
            raise ValidationError({'detail': f'Order is not in a state to accept offers. Current status: {order.order_status}'})

        # Get the offer to accept
        try:
            offer_to_accept = ProjectOffer.objects.get(offer_id=offer_id, order=order)
        except ProjectOffer.DoesNotExist:
            raise NotFound("Offer not found for this order.")

        # Ensure the offer is pending
        if offer_to_accept.status != 'pending':
            raise ValidationError({'detail': 'Only pending offers can be accepted.'})

        client_user = order.client_user
        technician_user = offer_to_accept.technician_user
        offered_price = offer_to_accept.offered_price

        # Implement atomic transaction for escrow
        with db_transaction.atomic():
            client_user.refresh_from_db() # Lock client user row
            technician_user.refresh_from_db() # Lock technician user row

            # Check if client has sufficient funds
            if client_user.available_balance < offered_price:
                raise ValidationError({'detail': 'Insufficient available balance to accept this offer.'})

            # Move funds from client's available balance to in_escrow_balance
            client_user.available_balance -= offered_price
            client_user.in_escrow_balance += offered_price
            client_user.save(update_fields=['available_balance', 'in_escrow_balance'])

            # Create an escrow hold transaction
            Transaction.objects.create(
                source_user=client_user,
                destination_user=technician_user,
                order=order,
                transaction_type='ESCROW_HOLD',
                amount=offered_price,
                currency='EGP',
                payment_method='Available Balance'
            )

            # Update the order
            order.technician_user = technician_user
            order.order_status = 'ACCEPTED' # Funds are now in escrow, job is accepted (Ensuring uppercase)
            order.final_price = offered_price # Set final price
            order.job_start_timestamp = datetime.now() # Mark job start
            # Set auto_release_date (e.g., 7 days from now)
            order.auto_release_date = datetime.now() + timedelta(days=7) # Example: 7 days for client to respond
            order.save()

            # Update offer statuses
            ProjectOffer.objects.filter(order=order).exclude(offer_id=offer_to_accept.offer_id).update(status='rejected')
            offer_to_accept.status = 'accepted'
            offer_to_accept.save()

            # Send notifications
            self._send_offer_notifications(order, offer_to_accept)

            serializer = self.get_serializer(order)
            return Response({
                'message': 'Offer accepted and funds moved to escrow successfully.',
                'order': serializer.data,
                'client_balance': {
                    'available_balance': client_user.available_balance,
                    'in_escrow_balance': client_user.in_escrow_balance,
                    'pending_balance': client_user.pending_balance,
                }
            }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsClientOwnerOrAdmin])
    def decline_offer(self, request, order_id=None, offer_id=None):
        """
        Decline a specific project offer for an order.
        Permissions: Authenticated Client User (owner of order) or Admin User.
        Usage: POST /api/orders/{order_id}/decline-offer/{offer_id}/
        """
        try:
            order = self.get_object()
        except Order.DoesNotExist:
            raise NotFound("Order not found.")

        # Check if user owns this order or is admin (already handled by permission_classes)
        
        # Get the offer to decline
        try:
            offer_to_decline = ProjectOffer.objects.get(offer_id=offer_id, order=order)
        except ProjectOffer.DoesNotExist:
            raise NotFound("Offer not found for this order.")

        # Ensure the offer is pending
        if offer_to_decline.status != 'pending':
            raise ValidationError({'detail': 'Only pending offers can be declined.'})

        with db_transaction.atomic():
            offer_to_decline.status = 'rejected'
            offer_to_decline.save()

            create_notification(
                user=offer_to_decline.technician_user,
                notification_type='offer_declined',
                title=ARABIC_NOTIFICATIONS['offer_declined_title'],
                message=ARABIC_NOTIFICATIONS['offer_declined_message'].format(order_id=order.order_id),
                related_order=order
            )
            
        serializer = self.get_serializer(order)
        return Response({
            'message': 'Offer declined successfully.',
            'order': serializer.data
        }, status=status.HTTP_200_OK)

    def _send_offer_notifications(self, order, accepted_offer):
        """Send notifications when an offer is accepted."""
        try:
            # Notify the accepted technician
            create_notification(
                user=accepted_offer.technician_user,
                notification_type='offer_accepted',
                title=ARABIC_NOTIFICATIONS['offer_accepted_title'],
                message=ARABIC_NOTIFICATIONS['offer_accepted_message'].format(order_id=order.order_id),
                related_order=order
            )

            # Notify rejected technicians
            rejected_offers = ProjectOffer.objects.filter(order=order).exclude(status='accepted') # Exclude accepted offer, check any status not accepted
            for rejected_offer in rejected_offers:
                create_notification(
                    user=rejected_offer.technician_user,
                    notification_type='offer_rejected',
                    title=ARABIC_NOTIFICATIONS['offer_rejected_title'],
                    message=ARABIC_NOTIFICATIONS['offer_rejected_message'].format(order_id=order.order_id),
                    related_order=order
                )

            # Notify the client
            create_notification(
                user=order.client_user,
                notification_type='offer_accepted',
                title=ARABIC_NOTIFICATIONS['offer_accepted_client_title'],
                message=ARABIC_NOTIFICATIONS['offer_accepted_client_message'].format(order_id=order.order_id),
                related_order=order
            )
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error sending notifications: {e}")

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsTechnicianOwnerOrAdmin])
    def start_job(self, request, order_id=None):
        """
        Allows an assigned technician to mark an order as 'IN_PROGRESS'.
        Permissions: Authenticated Technician User who is assigned to the order.
        Usage: POST /api/orders/{order_id}/start-job/
        """
        try:
            order = self.get_object()
        except Order.DoesNotExist:
            raise NotFound("Order not found.")

        # Ensure the authenticated user is the assigned technician
        if order.technician_user != request.user:
            raise PermissionDenied("You are not the assigned technician for this order.")

        # Ensure the order is in 'ACCEPTED' status
        if order.order_status != 'ACCEPTED':
            raise ValidationError({'detail': f'Order must be in "ACCEPTED" status to start the job. Current status: {order.order_status}'})

        with db_transaction.atomic():
            order.refresh_from_db()
            order.order_status = 'IN_PROGRESS'
            order.save(update_fields=['order_status'])

            create_notification(
                user=order.client_user,
                notification_type='job_started',
                title=ARABIC_NOTIFICATIONS['job_started_title'],
                message=ARABIC_NOTIFICATIONS['job_started_message'].format(technician_name=order.technician_user.get_full_name(), order_id=order.order_id),
                related_order=order
            )
        
        serializer = self.get_serializer(order)
        return Response({
            'message': 'Job started successfully. Order status updated to IN_PROGRESS.',
            'order': serializer.data
        }, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsTechnicianOwnerOrAdmin])
    def mark_job_done(self, request, order_id=None):
        """
        Allows a technician to mark a job as done.
        Transitions order status to 'AWAITING_RELEASE' and sets job_done_timestamp.
        Permissions: Authenticated Technician User who is assigned to the order.
        Usage: POST /api/orders/{order_id}/mark-job-done/
        """
        try:
            order = self.get_object()
        except Order.DoesNotExist:
            raise NotFound("Order not found.")

        # Ensure the authenticated user is the assigned technician
        if order.technician_user != request.user:
            raise PermissionDenied("You are not the assigned technician for this order.")

        # Ensure the order is in 'IN_PROGRESS' status
        if order.order_status != 'IN_PROGRESS': # Ensuring uppercase
            raise ValidationError({'detail': f'Order must be in "IN_PROGRESS" status to mark as done. Current status: {order.order_status}'})

        with db_transaction.atomic():
            order.refresh_from_db() # Lock order row
            order.order_status = 'AWAITING_RELEASE' # Ensuring uppercase
            order.job_done_timestamp = datetime.now()
            order.save(update_fields=['order_status', 'job_done_timestamp'])

            # Notify the client that the job is done
            create_notification(
                user=order.client_user,
                notification_type='job_done',
                title=ARABIC_NOTIFICATIONS['job_done_title'],
                message=ARABIC_NOTIFICATIONS['job_done_message'].format(technician_name=order.technician_user.get_full_name(), order_id=order.order_id),
                related_order=order
            )

        serializer = self.get_serializer(order)
        return Response({
            'message': 'Job marked as done successfully. Client notified to review.',
            'order': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsClientOwnerOrAdmin])
    def release_funds(self, request, order_id=None):
        """
        Allows a client to release funds for a completed job.
        Transitions order status to 'COMPLETED', moves funds from escrow to technician's pending balance.
        Permissions: Authenticated Client User who owns the order.
        Usage: POST /api/orders/{order_id}/release-funds/
        """
        try:
            order = self.get_object()
        except Order.DoesNotExist:
            raise NotFound("Order not found.")

        # Ensure the authenticated user is the client who owns the order
        if order.client_user != request.user:
            raise PermissionDenied("You are not the client for this order.")

        # Ensure the order is in 'AWAITING_RELEASE' status
        if order.order_status != 'AWAITING_RELEASE': # Ensuring uppercase
            raise ValidationError({'detail': f'Order must be in "AWAITING_RELEASE" status to release funds. Current status: {order.order_status}'})

        client_user = order.client_user
        technician_user = order.technician_user
        amount_to_release = order.final_price

        with db_transaction.atomic():
            client_user.refresh_from_db() # Lock client user row
            technician_user.refresh_from_db() # Lock technician user row
            order.refresh_from_db() # Lock order row

            # Platform Commission Logic (5%)
            gross_amount = order.final_price
            commission_rate = Decimal('0.05')
            platform_fee = gross_amount * commission_rate
            technician_payout = gross_amount - platform_fee

            # Ensure funds are in escrow
            if client_user.in_escrow_balance < gross_amount:
                # This should ideally not happen if escrow deposit was successful
                raise ValidationError({'detail': 'Error: Insufficient funds in escrow. Please contact support.'})

            # Move funds from client's in_escrow_balance
            client_user.in_escrow_balance -= gross_amount
            client_user.save(update_fields=['in_escrow_balance'])

            # Add NET amount to technician's pending_balance
            technician_user.pending_balance += technician_payout
            technician_user.save(update_fields=['pending_balance'])

            # Create Payout Transaction (To Technician)
            Transaction.objects.create(
                source_user=client_user,
                destination_user=technician_user,
                order=order,
                transaction_type='PAYOUT',
                amount=technician_payout,
                currency='EGP',
                payment_method='Escrow'
            )

            # Create Platform Fee Transaction (To System)
            Transaction.objects.create(
                source_user=client_user,
                destination_user=None, # System
                order=order,
                transaction_type='PLATFORM_FEE',
                amount=platform_fee,
                currency='EGP',
                payment_method='Escrow'
            )

            # Update the order status and financial records
            order.order_status = 'COMPLETED'
            order.job_completion_timestamp = datetime.now()
            order.commission_percentage = commission_rate * 100
            order.platform_commission_amount = platform_fee
            order.amount_to_technician = technician_payout
            order.save(update_fields=[
                'order_status', 
                'job_completion_timestamp', 
                'commission_percentage', 
                'platform_commission_amount', 
                'amount_to_technician'
            ])

        # Notify technician of fund release
        create_notification(
            user=technician_user,
            notification_type='funds_released',
            title=ARABIC_NOTIFICATIONS['funds_released_title'],
            message=ARABIC_NOTIFICATIONS['funds_released_message'].format(client_name=client_user.get_full_name(), order_id=order.order_id),
            related_order=order
        )

        # Update technician's statistics
        if technician_user:
            technician_user.update_stats()

        serializer = self.get_serializer(order)
        return Response({
            'message': 'Funds released successfully. Order marked as completed.',
            'order': serializer.data,
            'client_balance': {
                'available_balance': client_user.available_balance,
                'in_escrow_balance': client_user.in_escrow_balance,
                'pending_balance': client_user.pending_balance,
            },
            'technician_balance': {
                'available_balance': technician_user.available_balance,
                'in_escrow_balance': technician_user.in_escrow_balance,
                'pending_balance': technician_user.pending_balance,
            }
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsClientOwnerOrAdmin | IsTechnicianOwnerOrAdmin | IsAdminUser])
    def initiate_dispute(self, request, order_id=None):
        """
        Allows a client, assigned technician, or admin to initiate a dispute for an order.
        Transitions order status to 'DISPUTED' and creates a Dispute record.
        Permissions: Authenticated Client User who owns the order,
                     Authenticated Technician User who is assigned to the order, or Admin User.
        Usage: POST /api/orders/{order_id}/initiate-dispute/
        Body: {"argument": "Problem description."}
        """
        try:
            order = self.get_object()
        except Order.DoesNotExist:
            raise NotFound("Order not found.")

        # Ensure the authenticated user is either the client owner, assigned technician, or admin
        user = request.user
        if not (order.client_user == user or \
                (order.technician_user == user and user.user_type.user_type_name == 'technician') or \
                user.user_type.user_type_name == 'admin'):
            raise PermissionDenied("You do not have permission to initiate a dispute for this order.")

        # Ensure the order is in a state where a dispute can be initiated
        if order.order_status in ['DISPUTED', 'CANCELLED', 'REFUNDED', 'OPEN']: # No dispute for open, already disputed, or cancelled orders
            raise ValidationError({'detail': f'Dispute cannot be initiated for orders in current status: {order.order_status}'})

        argument = request.data.get('argument')
        if not argument:
            raise ValidationError({'argument': 'Dispute argument is required.'})
        
        # Ensure a technician is assigned if it's not an admin initiating
        if not order.technician_user and user.user_type.user_type_name != 'admin':
            raise ValidationError({'detail': 'Cannot initiate a dispute for an order without an assigned technician.'})

        with db_transaction.atomic():
            order.refresh_from_db() # Lock order row

            # Determine who is the initiator for the dispute record
            initiator_role = 'client' if order.client_user == user else ('technician' if order.technician_user == user else 'admin')

            dispute_fields = {
                'order': order,
                'initiator': user,
                'status': 'OPEN'
            }
            if initiator_role == 'client':
                dispute_fields['client_argument'] = argument
            elif initiator_role == 'technician':
                dispute_fields['technician_argument'] = argument
            else: # Admin can provide either, for simplicity, use admin_notes or a general field
                dispute_fields['admin_notes'] = f'Admin initiated dispute: {argument}'
            
            dispute = Dispute.objects.create(**dispute_fields)

            # Update order status
            order.order_status = 'DISPUTED'
            order.save(update_fields=['order_status'])

            # Send notifications
            if order.client_user != user: # Notify client if they are not the initiator
                create_notification(
                    user=order.client_user,
                    notification_type='dispute_initiated',
                    title=ARABIC_NOTIFICATIONS['dispute_initiated_title'],
                    message=ARABIC_NOTIFICATIONS['dispute_initiated_message'].format(user_name=user.get_full_name(), order_id=order.order_id),
                    related_order=order,
                    related_dispute=dispute
                )
            if order.technician_user and order.technician_user != user: # Notify technician if they are not the initiator
                create_notification(
                    user=order.technician_user,
                    notification_type='dispute_initiated',
                    title=ARABIC_NOTIFICATIONS['dispute_initiated_title'],
                    message=ARABIC_NOTIFICATIONS['dispute_initiated_message'].format(user_name=user.get_full_name(), order_id=order.order_id),
                    related_order=order,
                    related_dispute=dispute
                )
            # Notify all admins
            admins = User.objects.filter(user_type__user_type_name='admin')
            for admin_user in admins:
                if admin_user != user: # Don't notify admin if they are the initiator
                    create_notification(
                        user=admin_user,
                        notification_type='dispute_new',
                        title=ARABIC_NOTIFICATIONS['dispute_new_title'],
                        message=ARABIC_NOTIFICATIONS['dispute_new_message'].format(order_id=order.order_id, user_name=user.get_full_name()),
                        related_order=order,
                        related_dispute=dispute
                    )

        serializer = self.get_serializer(order)
        return Response({
            'message': 'Dispute initiated successfully. Relevant parties have been notified.',
            'order': serializer.data,
            'dispute_id': dispute.dispute_id
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def dispute_order(self, request, order_id=None):
        """
        Return order details for dispute purposes.
        Only accessible by the client who created the order, assigned technician, or admin.
        Permissions: Authenticated User (client owner, technician owner) or Admin User.
        Usage: GET /api/orders/{order_id}/dispute-order/
        """
        user = request.user
        
        # Use the same queryset logic as WorkerTasksViewSet to find orders for technicians
        # This ensures technicians can access orders where they are the technician_user
        try:
            order = Order.objects.select_related(
                'client_user', 
                'client_user__user_type',
                'technician_user', 
                'technician_user__user_type',
                'service'
            ).annotate(
                review_rating=models.F('review__rating'),
                review_comment=models.F('review__comment')
            ).prefetch_related(
                'project_offers',
                'project_offers__technician_user',
                'project_offers__technician_user__user_type',
                'disputes'
            ).get(order_id=order_id)
        except Order.DoesNotExist:
            raise NotFound("Order not found.")

        # Check if user has access to this order for dispute purposes
        if not (order.client_user == user or \
                (order.technician_user == user and user.user_type.user_type_name == 'technician') or \
                user.user_type.user_type_name == 'admin'):
            raise PermissionDenied("You don't have permission to view this order for dispute purposes.")

        # Serialize the order with full details
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsClientOwnerOrAdmin | IsAdminUser])
    def cancel_order(self, request, order_id=None):
        """
        Allows a client or admin to cancel an order.
        Handles fund refunds from escrow if applicable.
        Permissions: Authenticated Client User who owns the order, or Admin User.
        Usage: POST /api/orders/{order_id}/cancel-order/
        """
        try:
            order = self.get_object()
        except Order.DoesNotExist:
            raise NotFound("Order not found.")

        user = request.user
        is_client_owner = (order.client_user == user)
        is_admin = (user.user_type.user_type_name == 'admin')

        if not (is_client_owner or is_admin):
            raise PermissionDenied("You do not have permission to cancel this order.")
        
        # Ensure order is not already completed, disputed, or cancelled/refunded
        if order.order_status in ['COMPLETED', 'DISPUTED', 'CANCELLED', 'REFUNDED']:
            raise ValidationError({'detail': f'Order cannot be cancelled in current status: {order.order_status}'})

        with db_transaction.atomic():
            order.refresh_from_db() # Lock order row
            client_user = order.client_user
            technician_user = order.technician_user
            amount_in_escrow = order.final_price if order.final_price else Decimal('0.00')
            
            # If the order was accepted and funds are in escrow, refund them
            if order.order_status in ['ACCEPTED', 'IN_PROGRESS', 'AWAITING_RELEASE'] and amount_in_escrow > 0:
                client_user.refresh_from_db()
                
                if client_user.in_escrow_balance < amount_in_escrow:
                    raise ValidationError({'detail': 'Error: Insufficient funds in escrow for refund. Contact support.'})
                
                client_user.in_escrow_balance -= amount_in_escrow
                client_user.available_balance += amount_in_escrow # Refund to available balance
                client_user.save(update_fields=['in_escrow_balance', 'available_balance'])

                Transaction.objects.create(
                    source_user=client_user,
                    destination_user=client_user,
                    order=order,
                    transaction_type='CANCEL_REFUND',
                    amount=amount_in_escrow,
                currency='EGP',
                    payment_method='Escrow'
                )
                order.order_status = 'REFUNDED'
                message_to_client = ARABIC_NOTIFICATIONS['order_cancelled_refund_message'].format(order_id=order.order_id, amount=amount_in_escrow)
                message_to_technician = ARABIC_NOTIFICATIONS['order_cancelled_tech_message'].format(order_id=order.order_id, amount=amount_in_escrow)
            else:
                # If no funds in escrow (order was 'OPEN')
                order.order_status = 'CANCELLED'
                message_to_client = ARABIC_NOTIFICATIONS['order_cancelled_no_funds_message'].format(order_id=order.order_id)
                message_to_technician = ARABIC_NOTIFICATIONS['order_cancelled_tech_message'].format(order_id=order.order_id, amount='0.00')

            order.save(update_fields=['order_status'])

            # Send notifications
            create_notification(
                user=client_user,
                notification_type='order_cancelled',
                title=ARABIC_NOTIFICATIONS['order_cancelled_title'],
                message=message_to_client,
                related_order=order
            )
            if technician_user: # Only notify technician if one was assigned
                create_notification(
                    user=technician_user,
                    notification_type='order_cancelled',
                    title=ARABIC_NOTIFICATIONS['order_cancelled_title'],
                    message=message_to_technician,
                    related_order=order
                )
            
        serializer = self.get_serializer(order)
        return Response({
            'message': 'Order cancelled successfully.',
            'order': serializer.data,
            'client_balance': {
                'available_balance': client_user.available_balance,
                'in_escrow_balance': client_user.in_escrow_balance,
                'pending_balance': client_user.pending_balance,
            } if is_client_owner else None # Only show balance if client owns order
        }, status=status.HTTP_200_OK)


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

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAdminUser | IsTechnicianUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin)]
        else: # list, retrieve
            self.permission_classes = [IsAdminUser | (IsTechnicianUser & IsTechnicianOwnerOrAdmin) | (IsClientUser & IsClientOwnerOrAdmin)]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        
        base_queryset = ProjectOffer.objects.select_related(
            'technician_user', 
            'technician_user__user_type',
            'order',
            'order__client_user',
            'order__client_user__user_type',
            'order__service'
        )

        # Admins can see all offers
        if user.user_type.user_type_name == 'admin':
            return base_queryset

        # For specific actions like 'retrieve', 'update', 'partial_update', 'destroy',
        # and custom actions with detail=True, the default queryset is fine, 
        # and object-level permissions will handle access.
        if self.detail or self.action in ['update_client_offer', 'client_offers_for_technician']: # Add other detail=True/detail=False custom actions here that do their own filtering
            return base_queryset

        # For 'list' action and custom actions with detail=False that are not explicitly handled above, filter by user role
        if user.user_type.user_type_name == 'technician':
            # Technicians see their own project offers in the generic list
            return base_queryset.filter(technician_user=user)
        elif user.user_type.user_type_name == 'client':
            # Clients see offers related to their orders
            return base_queryset.filter(order__client_user=user)
        
        return ProjectOffer.objects.none() # Default for other user types or unauthenticated

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create project offers.")

        if user.user_type.user_type_name == 'technician':
            requested_technician_user_id = self.request.data.get('technician_user')
            if requested_technician_user_id and int(requested_technician_user_id) != user.user_id:
                raise PermissionDenied("Technicians can only create offers for themselves.")
            
            # Create the offer with all required fields
            offer = serializer.save(
                technician_user=user, 
                status='pending',
                offer_date=date.today()
            )
            
            # Send notification to client
            try:
                    create_notification(
                        user=offer.order.client_user,
                        notification_type='new_offer',
                        title=ARABIC_NOTIFICATIONS['new_offer_received_title'],
                        message=ARABIC_NOTIFICATIONS['new_offer_received_message'].format(order_id=offer.order.order_id),
                        related_order=offer.order
                    )
            except Exception as e:
                print(f"Error sending notification: {e}")
                
        elif user.user_type.user_type_name == 'admin':
            if 'technician_user' not in self.request.data:
                raise serializers.ValidationError({"technician_user": "This field is required for admin users."})
            serializer.save(status='pending', offer_date=date.today())
        else:
            raise PermissionDenied("Only technicians and admins can create project offers.")

    @action(detail=False, methods=['get'], permission_classes=[IsTechnicianUser])
    def client_offers_for_technician(self, request):
        """
        Return a list of client-initiated offers awaiting response for the authenticated technician.
        Includes complete order information for each offer.
        Permissions: Authenticated Technician User only.
        Usage: GET /api/orders/projectoffers/client-offers-for-technician/
        """
        user = request.user
        if not user.is_authenticated or user.user_type.user_type_name != 'technician':
            raise PermissionDenied("Only technicians can view client offers.")

        # Optimized queryset with comprehensive prefetching to minimize database queries
        client_offers = ProjectOffer.objects.filter(
            offer_initiator='client',
            technician_user=user,
            status='pending'
        ).select_related(
            'order',
            'order__client_user',
            'order__client_user__user_type',
            'order__service',
            'order__service__category',
            'technician_user',
            'technician_user__user_type'
        ).prefetch_related(
            'order__project_offers',
            'order__project_offers__technician_user',
            'order__project_offers__technician_user__user_type',
            'order__disputes',
            'order__client_user__user_type',
            'technician_user__user_type'
        ).order_by('-offer_date', '-offer_id')

        page = self.paginate_queryset(client_offers)
        if page is not None:
            serializer = ProjectOfferWithOrderSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ProjectOfferWithOrderSerializer(client_offers, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['put', 'patch'], permission_classes=[IsClientUser])
    def update_client_offer(self, request, offer_id=None, **kwargs): # Added offer_id to signature
        """
        Update a client-initiated offer. Only allowed if the offer is in 'pending' status.
        Permissions: Authenticated Client User (owner of the offer) only.
        Usage: PUT /api/orders/projectoffers/{offer_id}/update-client-offer/
        """
        try:
            offer = self.get_object()
        except ProjectOffer.DoesNotExist:
            raise NotFound("Offer not found.")

        # Check if the authenticated user is the creator of the offer and if it's client-initiated
        if (offer.order.client_user != request.user or offer.offer_initiator != 'client'):
            raise PermissionDenied("You can only update your own client-initiated offers.")

        # Check if the offer is in pending status
        if offer.status != 'pending':
            raise PermissionDenied("Cannot edit offer. Only pending offers can be edited.")

        # Separate order fields from offer fields
        order_fields = ['problem_description', 'requested_location', 'scheduled_date', 'scheduled_time_start', 'scheduled_time_end']
        offer_fields = ['offered_price', 'offer_description']
        
        order_data = {}
        offer_data = {}
        
        for key, value in request.data.items():
            if key in order_fields:
                order_data[key] = value
            elif key in offer_fields:
                offer_data[key] = value
            else:
                # If field doesn't belong to either, add it to offer data (for other offer-specific fields)
                offer_data[key] = value

        # Update the related order if order fields are provided
        if order_data:
            order_serializer = OrderSerializer(offer.order, data=order_data, partial=True)
            if order_serializer.is_valid():
                order_serializer.save()
            else:
                return Response(order_serializer.errors, status=400)

        # Update the offer with offer-specific data
        serializer = self.get_serializer(offer, data=offer_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Offer updated successfully.',
                'offer': serializer.data
            })
        return Response(serializer.errors, status=400)


class WorkerTasksViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows technicians to view their assigned tasks (orders).

    list:
    Return a list of orders assigned to the authenticated technician.
    Supports filtering by order_status using order_status__in parameter (e.g., ?order_status__in=pending,in_progress)
    Supports limiting results using limit parameter (e.g., ?limit=3)
    Supports pagination using page and page_size parameters (e.g., ?page=1&page_size=10)
    Permissions: Authenticated Technician User only.
    Usage: GET /api/orders/worker-tasks/
    Usage: GET /api/orders/worker-tasks/?order_status__in=pending,in_progress&limit=3
    Usage: GET /api/orders/worker-tasks/?has_dispute=true&page=1&page_size=10

    retrieve:
    Return a specific order assigned to the authenticated technician.
    Permissions: Authenticated Technician User only.
    Usage: GET /api/orders/worker-tasks/{order_id}/
    """
    serializer_class = OrderSerializer
    lookup_field = 'order_id'
    pagination_class = OrderPagination

    def get_permissions(self):
        self.permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none()

        # All authenticated users can access this endpoint, but only technicians will have assigned orders.
        # The queryset will naturally filter for orders where technician_user=user.
        # No explicit check for user_type is needed here.

        # Start with orders assigned to this technician
        queryset = Order.objects.filter(technician_user=user).select_related(
            'client_user', 
            'client_user__user_type',
            'technician_user', 
            'technician_user__user_type',
            'service'
        ).annotate(
            review_rating=models.F('review__rating'),
            review_comment=models.F('review__comment')
        ).prefetch_related(
            'project_offers',
            'project_offers__technician_user',
            'project_offers__technician_user__user_type',
            'disputes'  # Add disputes prefetch for the has_dispute filter
            # Remove 'review' from prefetch_related as we're using annotations
        )

        # Check if we want orders with disputes only
        has_dispute = self.request.query_params.get('has_dispute')
        if has_dispute and has_dispute.lower() == 'true':
            queryset = queryset.filter(disputes__isnull=False).distinct()

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

        # Add single order_status filter for WorkerTasksViewSet
        order_status = self.request.query_params.get('order_status')
        if order_status:
            queryset = queryset.filter(order_status=order_status)

        # Apply limit if provided - must do this before ordering
        limit = self.request.query_params.get('limit')
        if limit and limit.isdigit():
            queryset = queryset.order_by('-order_id')[:int(limit)] # Sorted by order_id descending
        else:
            # Always order by creation date, most recent first
            queryset = queryset.order_by('-order_id') # Sorted by order_id descending

        return queryset
