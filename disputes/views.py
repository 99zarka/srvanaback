from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction as db_transaction
from django.utils import timezone
from decimal import Decimal # Import Decimal
from .models import Dispute, DisputeResponse
from .serializers import DisputeSerializer, DisputeResponseSerializer
from api.permissions import IsAdminUser, IsClientUser, IsTechnicianUser, IsDisputeParticipantOrAdmin # Added IsDisputeParticipantOrAdmin
from notifications.utils import create_notification
from notifications.arabic_translations import ARABIC_NOTIFICATIONS
from users.models import User
from transactions.models import Transaction
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from rest_framework import generics # Added generics for get_object_or_404

class DisputeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Disputes to be viewed, created, or resolved.

    list:
    Return a list of disputes for the authenticated user (client or technician) or all disputes for admin.
    Permissions: Authenticated User (client/technician involved) or Admin User.
    Usage: GET /api/disputes/

    retrieve:
    Return a specific dispute by ID.
    Permissions: Authenticated User (client/technician involved) or Admin User.
    Usage: GET /api/disputes/{dispute_id}/

    create:
    Create a new dispute. (Generally, disputes are initiated via Order.initiate_dispute, but admin can create directly.)
    Permissions: Admin User.
    Usage: POST /api/disputes/
    Body: {"order": 1, "initiator": 2, "client_argument": "Client claims work was not done."}

    update:
    Update an existing dispute.
    Permissions: Admin User.
    Usage: PUT /api/disputes/{dispute_id}/
    Body: {"status": "IN_REVIEW", "admin_notes": "Admin investigating."}

    partial_update:
    Partially update an existing dispute.
    Permissions: Admin User.
    Usage: PATCH /api/disputes/{dispute_id}/
    Body: {"status": "IN_REVIEW"}

    destroy:
    Delete a dispute.
    Permissions: Admin User.
    Usage: DELETE /api/disputes/{dispute_id}/

    resolve:
    Resolve a specific dispute, updating status, recording resolution, and handling fund transfers.
    Permissions: Admin User.
    Usage: POST /api/disputes/{dispute_id}/resolve/
    Body: {"resolution": "REFUND_CLIENT", "client_refund_amount": 50.00, "admin_notes": "Partial refund due to incomplete work."}
    """
    queryset = Dispute.objects.all().order_by('-created_at')
    serializer_class = DisputeSerializer
    lookup_field = 'dispute_id'

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'resolve']:
            self.permission_classes = [IsAdminUser]
        elif self.action == 'list':
            # For list, we still filter by queryset based on user role
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'retrieve':
            # For retrieve, we want to find the object first, then apply object-level permission
            self.permission_classes = [permissions.IsAuthenticated, IsDisputeParticipantOrAdmin]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        # Base queryset for all actions (except retrieve, which overrides get_object)
        user = self.request.user
        if not user.is_authenticated:
            return Dispute.objects.none()

        if self.action == 'list':
            if user.user_type.user_type_name == 'admin':
                return Dispute.objects.all().order_by('-created_at')
            # Changed to filter for both initiator (client) and technician_user (from related order)
            elif user.user_type.user_type_name == 'client':
                return Dispute.objects.filter(initiator=user).order_by('-created_at')
            elif user.user_type.user_type_name == 'technician':
                return Dispute.objects.filter(order__technician_user=user).order_by('-created_at')
            return Dispute.objects.none()
        
        # For other actions like retrieve (handled by get_object overriding this), or actions that require admin only
        # The default queryset should be all objects, then permissions handle access
        return Dispute.objects.all()

    def get_object(self):
        # This is overridden to ensure object-level permissions are always checked
        # by fetching the object from the *full* queryset, then letting DRF's
        # check_object_permissions handle the 403.
        queryset = Dispute.objects.all() # Fetch from unfiltered queryset
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {lookup_url_kwarg: self.kwargs[lookup_url_kwarg]}
        obj = generics.get_object_or_404(queryset, **filter_kwargs)

        # Ensure the permissions checks are run against the object
        self.check_object_permissions(self.request, obj)
        return obj

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def resolve(self, request, dispute_id=None): # Renamed action from resolve_dispute to resolve
        """
        Allows an admin to resolve a dispute.
        Handles fund transfers, updates dispute status and records resolution details.
        Permissions: Admin User.
        Usage: POST /api/disputes/{dispute_id}/resolve/
        Body: {
            "resolution": "PAY_TECHNICIAN" | "REFUND_CLIENT" | "SPLIT_PAYMENT",
            "admin_notes": "Admin's decision based on evidence." (required),
            "client_refund_amount": 50.00 (required for SPLIT_PAYMENT),
            "technician_payout_amount": 50.00 (required for SPLIT_PAYMENT)
        }
        """
        try:
            dispute = self.get_object()
        except NotFound:
            raise NotFound("Dispute not found.")

        if dispute.status == 'RESOLVED':
            raise ValidationError({'detail': 'This dispute has already been resolved.'})

        resolution = request.data.get('resolution')
        admin_notes = request.data.get('admin_notes')
        client_refund_amount = request.data.get('client_refund_amount', Decimal('0.00'))
        technician_payout_amount = request.data.get('technician_payout_amount', Decimal('0.00'))

        if not resolution or not admin_notes:
            raise ValidationError({'detail': 'Resolution and admin_notes are required.'})
        
        if resolution not in [choice[0] for choice in Dispute.RESOLUTION_CHOICES]:
            raise ValidationError({'resolution': f'Invalid resolution choice. Must be one of: {[choice[0] for choice in Dispute.RESOLUTION_CHOICES]}'})

        # Ensure numeric amounts are Decimal
        try:
            client_refund_amount = Decimal(str(client_refund_amount))
            technician_payout_amount = Decimal(str(technician_payout_amount))
        except (ValueError, TypeError):
            raise ValidationError({'detail': 'Resolved amounts must be valid numbers for split payment.'})

        order = dispute.order
        # Use the order's actual client user, not the dispute initiator
        client_user = order.client_user
        # Technician is associated with the order, not directly the dispute model anymore
        technician_user = order.technician_user
        admin_user = request.user
        
        # Assuming order.final_price is the amount held in escrow
        amount_in_escrow = order.final_price if order.final_price else Decimal('0.00')

        with db_transaction.atomic():
            client_user.refresh_from_db()
            if technician_user:
                technician_user.refresh_from_db()
            order.refresh_from_db()
            dispute.refresh_from_db()

            total_split_amount = client_refund_amount + technician_payout_amount

            if resolution == 'REFUND_CLIENT':
                if amount_in_escrow > 0:
                    if client_user.in_escrow_balance < amount_in_escrow:
                        raise ValidationError({'detail': 'Error: Insufficient funds in client escrow for full refund. Contact support.'})
                    
                    client_user.in_escrow_balance -= amount_in_escrow
                    client_user.available_balance += amount_in_escrow
                    client_user.save(update_fields=['in_escrow_balance', 'available_balance'])
                    
                    Transaction.objects.create(
                        source_user=client_user,
                        destination_user=client_user, # Funds returned to same user
                        order=order,
                        dispute=dispute,
                        transaction_type='DISPUTE_REFUND',
                        amount=amount_in_escrow,
                        currency='EGP',
                        payment_method='Escrow'
                    )
                order.order_status = 'REFUNDED'

            elif resolution == 'PAY_TECHNICIAN':
                if amount_in_escrow > 0:
                    if client_user.in_escrow_balance < amount_in_escrow:
                        raise ValidationError({'detail': 'Error: Insufficient funds in client escrow for technician payout. Contact support.'})
                    
                    client_user.in_escrow_balance -= amount_in_escrow
                    client_user.save(update_fields=['in_escrow_balance'])
                    if technician_user:
                        technician_user.pending_balance += amount_in_escrow
                        technician_user.save(update_fields=['pending_balance'])
                    
                    Transaction.objects.create(
                        source_user=client_user,
                        destination_user=technician_user,
                        order=order,
                        dispute=dispute,
                        transaction_type='DISPUTE_PAYOUT',
                        amount=amount_in_escrow,
                        currency='EGP',
                        payment_method='Escrow'
                    )
                order.order_status = 'COMPLETED'
                order.job_completion_timestamp = timezone.now() # Mark job completed upon resolution

            elif resolution == 'SPLIT_PAYMENT':
                if total_split_amount > amount_in_escrow:
                    raise ValidationError({'detail': 'Total split amounts exceed the escrowed amount.'})
                
                if client_user.in_escrow_balance < total_split_amount: # Check against total split amount, not full escrow
                    raise ValidationError({'detail': 'Error: Insufficient funds in client escrow for split payment. Contact support.'})

                # Refund client portion
                if client_refund_amount > Decimal('0.00'):
                    client_user.in_escrow_balance -= client_refund_amount
                    client_user.available_balance += client_refund_amount
                    client_user.save(update_fields=['in_escrow_balance', 'available_balance'])
                    Transaction.objects.create(
                        source_user=client_user,
                        destination_user=client_user,
                        order=order,
                        dispute=dispute,
                        transaction_type='DISPUTE_REFUND',
                        amount=client_refund_amount,
                        currency='EGP',
                        payment_method='Escrow'
                    )

                # Pay technician portion
                if technician_payout_amount > Decimal('0.00'):
                    client_user.in_escrow_balance -= technician_payout_amount
                    client_user.save(update_fields=['in_escrow_balance'])
                    if technician_user:
                        technician_user.pending_balance += technician_payout_amount
                        technician_user.save(update_fields=['pending_balance'])
                    Transaction.objects.create(
                        source_user=client_user,
                        destination_user=technician_user,
                        order=order,
                        dispute=dispute,
                        transaction_type='DISPUTE_PAYOUT',
                        amount=technician_payout_amount,
                        currency='EGP',
                        payment_method='Escrow'
                    )
                
                # Any remaining escrow after split (should be zero if total_split_amount = amount_in_escrow)
                remaining_escrow = amount_in_escrow - total_split_amount
                if remaining_escrow > Decimal('0.00'):
                    # This case should ideally not happen if split amounts are handled correctly
                    # For safety, return any small remainder to client
                    client_user.in_escrow_balance -= remaining_escrow
                    client_user.available_balance += remaining_escrow
                    client_user.save(update_fields=['in_escrow_balance', 'available_balance'])
                    Transaction.objects.create(
                        source_user=client_user,
                        destination_user=client_user,
                        order=order,
                        dispute=dispute,
                        transaction_type='DISPUTE_REFUND', # Or a specific 'DISPUTE_REMAINDER'
                        amount=remaining_escrow,
                        currency='EGP',
                        payment_method='Escrow'
                    )

                order.order_status = 'COMPLETED'
                order.job_completion_timestamp = timezone.now()

            # Update dispute record
            dispute.status = 'RESOLVED'
            dispute.admin_notes = admin_notes # Updated field name
            dispute.resolution = resolution
            dispute.resolution_date = timezone.now()
            dispute.save()

            order.save(update_fields=['order_status', 'job_completion_timestamp'])

            # Send notifications
            create_notification(
                user=client_user,
                notification_type='dispute_resolved',
                title=ARABIC_NOTIFICATIONS['dispute_resolved_title'],
                message=ARABIC_NOTIFICATIONS['dispute_resolved_message'].format(order_id=order.order_id, resolution=resolution, details=admin_notes),
                related_order=order
            )
            if technician_user:
                create_notification(
                    user=technician_user,
                    notification_type='dispute_resolved',
                    title=ARABIC_NOTIFICATIONS['dispute_resolved_title'],
                    message=ARABIC_NOTIFICATIONS['dispute_resolved_message'].format(order_id=order.order_id, resolution=resolution, details=admin_notes),
                    related_order=order
                )

        serializer = self.get_serializer(dispute)
        return Response({
            'message': 'Dispute resolved successfully. Funds transferred and parties notified.',
            'dispute': serializer.data,
            'client_balance': {
                'available_balance': client_user.available_balance,
                'in_escrow_balance': client_user.in_escrow_balance,
                'pending_balance': client_user.pending_balance,
            },
            'technician_balance': {
                'available_balance': technician_user.available_balance,
                'in_escrow_balance': technician_user.in_escrow_balance,
                'pending_balance': technician_user.pending_balance,
            } if technician_user else None
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_response(self, request, dispute_id=None):
        """
        Allows a dispute participant (client or technician) to add a response to the dispute.
        Permissions: Authenticated User (client or technician involved in the dispute)
        Usage: POST /api/disputes/{dispute_id}/add_response/
        Body: {"message": "Your response message here", "file_url": file_data}
        """
        try:
            dispute = self.get_object()
        except NotFound:
            raise NotFound("Dispute not found.")

        # Check if the user is a participant in the dispute
        user = request.user
        order = dispute.order

        # Determine if user is client or technician
        is_client = user == dispute.initiator  # initiator is the client in the dispute
        is_technician = user == order.technician_user
        is_admin = user.user_type.user_type_name == 'admin'

        if not (is_client or is_technician or is_admin):
            raise PermissionDenied("You are not authorized to respond to this dispute.")

        # Determine response type based on user role
        if is_client:
            response_type = 'CLIENT'
        elif is_technician:
            response_type = 'TECHNICIAN'
        else: # admin
            response_type = 'ADMIN'

        # Validate request data
        message = request.data.get('message')
        file_url = request.data.get('file_url')

        if not message and not file_url:
            raise ValidationError({'error': 'Either message or file is required.'})

        # Create the dispute response
        response = DisputeResponse.objects.create(
            dispute=dispute,
            sender=user,
            response_type=response_type,
            message=message,
            file_url=file_url  # This will be handled by CloudinaryField
        )

        # Update dispute status to IN_REVIEW if it's currently OPEN
        if dispute.status == 'OPEN':
            dispute.status = 'IN_REVIEW'
            dispute.save(update_fields=['status'])

        # Send notification to other participants
        participants_to_notify = []
        if is_client and order.technician_user:
            participants_to_notify.append(order.technician_user)
        elif is_technician:
            participants_to_notify.append(dispute.initiator)
        elif is_admin:
            # Notify both client and technician
            participants_to_notify.append(dispute.initiator)
            if order.technician_user:
                participants_to_notify.append(order.technician_user)

        for participant in participants_to_notify:
            if participant != user:  # Don't notify the sender
                create_notification(
                    user=participant,
                    notification_type='dispute_response',
                    title=ARABIC_NOTIFICATIONS['dispute_response_title'],
                    message=ARABIC_NOTIFICATIONS['dispute_response_message'].format(dispute_id=dispute.dispute_id, order_id=order.order_id),
                    related_order=order,
                    related_dispute=dispute
                )

        # Return the created response with updated dispute data
        response_serializer = DisputeResponseSerializer(response)
        dispute_serializer = DisputeSerializer(dispute)
        return Response({
            'message': 'Response added successfully.',
            'response': response_serializer.data,
            'dispute': dispute_serializer.data
        }, status=status.HTTP_201_CREATED)
