from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from users.models import User, UserType
from users.serializers import UserTypeSerializer, UserSerializer, PublicUserSerializer
from api.permissions import IsAdminUser, IsOwnerOrAdmin, IsClientUser, IsTechnicianUser
from api.mixins import OwnerFilteredQuerysetMixin
from orders.models import Order, ProjectOffer
from orders.serializers import OrderSerializer, ClientMakeOfferSerializer, ProjectOfferSerializer
from notifications.models import Notification
from notifications.utils import create_notification
from notifications.arabic_translations import ARABIC_NOTIFICATIONS
from datetime import date
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from services.models import Service

class UserPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class UserTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows UserTypes to be viewed or edited.

    list:
    Return a list of all user types.
    Usage: GET /api/usertypes/

    retrieve:
    Return a specific user type by ID.
    Usage: GET /api/usertypes/{id}/

    create:
    Create a new user type. (Admin only)
    Usage: POST /api/usertypes/
    Body: {"name": "New User Type"}

    update:
    Update an existing user type. (Admin only)
    Usage: PUT /api/usertypes/{id}/
    Body: {"name": "Updated User Type"}

    partial_update:
    Partially update an existing user type. (Admin only)
    Usage: PATCH /api/usertypes/{id}/
    Body: {"name": "Partially Updated User Type"}

    destroy:
    Delete a user type. (Admin only)
    Usage: DELETE /api/usertypes/{id}/
    """
    queryset = UserType.objects.all().order_by('user_type_id')
    serializer_class = UserTypeSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        else: # list, retrieve
            self.permission_classes = [permissions.AllowAny] # Publicly accessible
        return super().get_permissions()

class UserViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Users to be viewed or edited.

    list:
    Return a list of all users. Requires authentication.
    Usage: GET /api/users/

    retrieve:
    Return a specific user by ID. Requires authentication and either admin privileges or ownership.
    Usage: GET /api/users/{id}/

    create:
    Create a new user. This is typically handled by a separate registration endpoint.
    Usage: POST /api/users/
    Body: {"username": "newuser", "email": "new@example.com", "password": "password123"}

    update:
    Update an existing user. Requires authentication and either admin privileges or ownership.
    Usage: PUT /api/users/{id}/
    Body: {"email": "updated@example.com"}

    partial_update:
    Partially update an existing user. Requires authentication and either admin privileges or ownership.
    Usage: PATCH /api/users/{id}/
    Body: {"username": "updatedusername"}

    destroy:
    Delete a user. Requires authentication and either admin privileges or ownership.
    Usage: DELETE /api/users/{id}/

    technician_detail:
    Return detailed information about a specific technician.
    Permissions: Any authenticated user or public access.
    Usage: GET /api/users/technician-detail/{user_id}/

    make_offer_to_technician:
    Client makes a direct offer to a specific technician.
    Permissions: Authenticated Client User.
    Usage: POST /api/users/{technician_id}/make-offer-to-technician/
    Body: {"service_id": 1, "offered_price": 200.00, "problem_description": "Fix my sink", "requested_location": "123 Main St", "scheduled_date": "2025-12-25", "scheduled_time_start": "09:00", "scheduled_time_end": "11:00"}

    respond_to_client_offer:
    Technician responds to a client's direct offer (accept/reject).
    Permissions: Authenticated Technician User (owner of the offer).
    Usage: POST /api/users/offers/{offer_id}/respond-to-client-offer/
    Body: {"action": "accept" or "reject", "rejection_reason": "Not available" (optional for reject)}
    """
    pagination_class = UserPagination
    queryset = User.objects.all().order_by('user_id')
    serializer_class = UserSerializer
    owner_field = 'user_id'

    def get_permissions(self):
        if self.action == 'list':
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsOwnerOrAdmin)]
        elif self.action == 'technician_detail':
            self.permission_classes = [permissions.AllowAny]
        elif self.action == 'create':
            self.permission_classes = [IsAdminUser | permissions.AllowAny]
        elif self.action == 'make_offer_to_technician':
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'respond_to_client_offer':
            self.permission_classes = [IsTechnicianUser]
        return super().get_permissions()

    def get_filtered_queryset(self, user, base_queryset):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return base_queryset
        return base_queryset

    @action(detail=True, methods=['get'])
    def technician_detail(self, request, pk=None):
        """
        Get detailed information about a specific technician.
        """
        try:
            technician = User.objects.get(
                user_id=pk,
                user_type__user_type_name='technician',
            )
        except User.DoesNotExist:
            return Response({'detail': 'Technician not found.'}, status=404)

        serializer = PublicUserSerializer(technician, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='make-offer-to-technician')
    def make_offer_to_technician(self, request, pk=None):
        """
        Client makes a direct offer to a specific technician.
        This action will create an Order and a ProjectOffer using a nested serializer.
        """
        offer_initiator_user = request.user
        if not offer_initiator_user.is_authenticated:
            raise PermissionDenied("Only authenticated users can make offers to technicians.")

        if not hasattr(offer_initiator_user, 'user_type') or not offer_initiator_user.user_type:
            raise PermissionDenied("User does not have an assigned user type.")

        try:
            technician_user = User.objects.get(
                user_id=pk,
                user_type__user_type_name='technician',
            )
        except User.DoesNotExist:
            raise NotFound("Technician not found.")

        if offer_initiator_user.user_id == technician_user.user_id:
            raise ValidationError("You cannot make an offer to yourself.")

        # Use the ClientMakeOfferSerializer to handle the nested creation
        serializer = ClientMakeOfferSerializer(
            data={
                **request.data,
                'technician_user': technician_user.user_id # Ensure technician_user is in data
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        offer = serializer.save() # The create method in the serializer handles Order and ProjectOffer creation

        # Extract order and technician from the created offer for notification and response
        order = offer.order
        
        # Send notification to the technician
        try:
            create_notification(
                user=technician_user,
                notification_type='new_direct_offer',
                title=ARABIC_NOTIFICATIONS['new_direct_offer_title'],
                message=ARABIC_NOTIFICATIONS['new_direct_offer_message'].format(user_name=offer_initiator_user.get_full_name(), order_id=order.order_id),
                related_order=order,
                related_offer=offer
            )
        except Exception as e:
            print(f"Error sending notification for new client offer: {e}")

        return Response({
            'message': 'Offer sent to technician successfully.',
            'order': OrderSerializer(order, context={'request': request}).data,
            'offer': ProjectOfferSerializer(offer, context={'request': request}).data
        }, status=201)

    @action(detail=True, methods=['post'], url_path='offers/(?P<offer_id>[^/.]+)/respond-to-client-offer')
    def respond_to_client_offer(self, request, pk=None, offer_id=None):
        """
        Technician responds to a client's direct offer (accept/reject).
        """
        technician_user = request.user
        if not technician_user.is_authenticated or technician_user.user_type.user_type_name != 'technician':
            raise PermissionDenied("Only authenticated technicians can respond to client offers.")

        try:
            offer = ProjectOffer.objects.get(
                offer_id=offer_id,
                technician_user=technician_user,
                offer_initiator='client',
                status='pending'
            )
        except ProjectOffer.DoesNotExist:
            raise NotFound("Pending client offer not found for this technician.")

        action_type = request.data.get('action')
        if action_type not in ['accept', 'reject']:
            raise ValidationError({"action": "Action must be 'accept' or 'reject'."})

        order = offer.order

        if action_type == 'accept':
            order.technician_user = technician_user
            order.order_status = 'AWAITING_CLIENT_ESCROW_CONFIRMATION'
            order.save()

            # The offer status remains 'pending' until the client accepts and funds the escrow.
            # offer.status = 'accepted' # COMMENTED OUT: Offer status should remain pending here
            # offer.save() # No need to save offer if status isn't changing

            message = 'Offer accepted successfully, awaiting client fund confirmation.'
            notification_type = 'direct_offer_accepted_by_tech' # Consider a more specific notification type
            notification_title = 'Technician Accepted Your Direct Offer!'
            notification_message = (
                f'Technician {technician_user.get_full_name()} has accepted your direct offer for order #{order.order_id}. '
                'Please proceed to your dashboard to confirm the offer and fund the escrow to secure the service.'
            )
            create_notification(
                user=order.client_user,
                notification_type=notification_type,
                title=ARABIC_NOTIFICATIONS['direct_offer_accepted_title'],
                message=ARABIC_NOTIFICATIONS['direct_offer_accepted_message'].format(technician_name=technician_user.get_full_name(), order_id=order.order_id),
                related_order=order,
                related_offer=offer
            )

        else: # action_type == 'reject'
            rejection_reason = request.data.get('rejection_reason', 'No reason provided.')
            offer.status = 'rejected'
            offer.offer_description = f"{offer.offer_description} (Rejected: {rejection_reason})"
            offer.save()

            # For rejection, consider if the order status should revert or become 'CLIENT_OFFER_REJECTED'
            # For now, let's keep it simple and just mark the offer as rejected.
            # The client would then likely just cancel the order or ignore it.
            # order.order_status = 'rejected' # Removed this line as it could conflict with other flows
            # order.save() # If order status isn't changed, no need to save order here for rejection

            message = 'Offer rejected successfully.'
            notification_type = 'client_offer_rejected'
            notification_title = 'Your Direct Offer Was Rejected'
            notification_message = f'Technician {technician_user.get_full_name()} has rejected your direct offer for order #{order.order_id}. Reason: {rejection_reason}'
            create_notification(
                user=order.client_user,
                notification_type=notification_type,
                title=ARABIC_NOTIFICATIONS['direct_offer_rejected_title'],
                message=ARABIC_NOTIFICATIONS['direct_offer_rejected_message'].format(technician_name=technician_user.get_full_name(), order_id=order.order_id, reason=rejection_reason),
                related_order=order,
                related_offer=offer
            )


        response_data = {
            'message': message,
            'offer': ProjectOfferSerializer(offer, context={'request': request}).data,
        }
        if action_type == 'accept':
            response_data['order_status'] = order.order_status # Include the updated order_status
        return Response(response_data, status=200)


class PublicUserViewSet(UserViewSet):
    """
    Public API endpoint to list users (for directory/search).
    """
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        return [permissions.AllowAny()]
