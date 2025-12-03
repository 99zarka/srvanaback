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
from notifications.models import Notification # Keep this for now, will replace usage with utils
from notifications.utils import create_notification # Import the helper function
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
            self.permission_classes = [permissions.IsAuthenticated] # Only authenticated users can list
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsOwnerOrAdmin)] # Only admin or owner can retrieve/update/delete
        elif self.action == 'technician_detail':
            self.permission_classes = [permissions.AllowAny] # Public access for browsing technicians
        elif self.action == 'create':
            self.permission_classes = [IsAdminUser | permissions.AllowAny] # Allow any user to create an account (handled by RegisterView)
        elif self.action == 'make_offer_to_technician':
            # Updated permission to allow any authenticated user to make an offer
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'respond_to_client_offer':
            self.permission_classes = [IsTechnicianUser] # Only technicians can respond to offers made to them
        return super().get_permissions()

    def get_filtered_queryset(self, user, base_queryset):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            # For these actions, return the full queryset and let object-level permissions handle access
            return base_queryset
        # For 'list' action, return all users (no filtering by owner)
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
                # Removed verification_status filter as per user instruction
            )
        except User.DoesNotExist:
            return Response({'detail': 'Technician not found.'}, status=404)

        serializer = PublicUserSerializer(technician, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='make-offer-to-technician')
    def make_offer_to_technician(self, request, pk=None):
        """
        Client makes a direct offer to a specific technician.
        This action will create an Order and a ProjectOffer.
        """
        # Renamed client_user to offer_initiator_user as any authenticated user can now make an offer
        offer_initiator_user = request.user
        if not offer_initiator_user.is_authenticated:
            raise PermissionDenied("Only authenticated users can make offers to technicians.")

        # Ensure the offer_initiator_user has a valid user_type.
        # This check prevents issues if a user somehow doesn't have a user_type assigned.
        if not hasattr(offer_initiator_user, 'user_type') or not offer_initiator_user.user_type:
            raise PermissionDenied("User does not have an assigned user type.")

        try:
            technician_user = User.objects.get(
                user_id=pk,
                user_type__user_type_name='technician',
                # Removed verification_status filter as per user instruction
            )
        except User.DoesNotExist:
            raise NotFound("Technician not found.")

        # Prevent a user from making an offer to themselves
        if offer_initiator_user.user_id == technician_user.user_id:
            raise ValidationError("You cannot make an offer to yourself.")

        service_id = request.data.get('service_id')
        if not service_id:
            raise ValidationError({"service_id": "Service ID is required to make an offer."})
        
        try:
            service_instance = Service.objects.get(service_id=service_id)
        except Service.DoesNotExist:
            raise NotFound("Service not found.")

        # Data for creating the Order
        order_data = {
            # 'service': service_instance, # Handled by serializer.save()
            'problem_description': request.data.get('problem_description'),
            'requested_location': request.data.get('requested_location'),
            'scheduled_date': request.data.get('scheduled_date'),
            'scheduled_time_start': request.data.get('scheduled_time_start'),
            'scheduled_time_end': request.data.get('scheduled_time_end'),
            'order_type': 'direct_hire', # Indicate this order is from a direct hire
            'creation_timestamp': date.today(),
            'order_status': 'awaiting_technician_response', # New status for client-initiated offers
            # 'client_user': offer_initiator_user.user_id, # Use offer_initiator_user as client_user for the order
        }

        order_serializer = OrderSerializer(data=order_data, context={'request': request})
        order_serializer.is_valid(raise_exception=True)
        order = order_serializer.save(client_user=offer_initiator_user, service=service_instance) # Save with offer_initiator_user and service instance

        # Data for creating the ProjectOffer
        offer_data = {
            'order': order.order_id,
            'technician_user_id': technician_user.user_id,
            'offered_price': request.data.get('offered_price'),
            'offer_description': request.data.get('offer_description', f"Direct offer for {order.problem_description}"),
            'offer_date': date.today(),
            'status': 'pending', # Pending technician's response
        }

        offer_serializer = ClientMakeOfferSerializer(data=offer_data, context={'request': request})
        offer_serializer.is_valid(raise_exception=True)
        offer = offer_serializer.save(
            order=order,
            technician_user=technician_user,
            offer_initiator='client', # Set the initiator as client
            status='pending',
            offer_date=date.today()
        )

        # Send notification to the technician
        try:
            create_notification( # Using the helper function
                user=technician_user,
                notification_type='new_direct_offer',
                title='New Direct Offer Received',
                message=f'User {offer_initiator_user.get_full_name()} has made a direct offer for order #{order.order_id}.',
                related_order=order,
                related_offer=offer # Pass the related offer
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
        The 'pk' in this case refers to the technician's user_id, which we use for permission check.
        """
        technician_user = request.user
        if not technician_user.is_authenticated or technician_user.user_type.user_type_name != 'technician':
            raise PermissionDenied("Only authenticated technicians can respond to client offers.")

        try:
            offer = ProjectOffer.objects.get(
                offer_id=offer_id,
                technician_user=technician_user,
                offer_initiator='client',
                status='pending' # Only pending offers can be responded to
            )
        except ProjectOffer.DoesNotExist:
            raise NotFound("Pending client offer not found for this technician.")

        action_type = request.data.get('action') # 'accept' or 'reject'
        if action_type not in ['accept', 'reject']:
            raise ValidationError({"action": "Action must be 'accept' or 'reject'."})

        order = offer.order

        if action_type == 'accept':
            # Assign technician to the order and update status
            order.technician_user = technician_user
            order.order_status = 'accepted'
            order.save()

            # Update offer status
            offer.status = 'accepted'
            offer.save()

            message = 'Offer accepted successfully.'
            notification_type = 'client_offer_accepted'
            notification_title = 'Your Direct Offer Was Accepted!'
            notification_message = f'Technician {technician_user.get_full_name()} has accepted your direct offer for order #{order.order_id}.'

        else: # action_type == 'reject'
            rejection_reason = request.data.get('rejection_reason', 'No reason provided.')
            offer.status = 'rejected'
            offer.offer_description = f"{offer.offer_description} (Rejected: {rejection_reason})"
            offer.save()

            # When a technician rejects a direct offer, the order status should change to 'rejected'.
            # The client can then decide to create a new offer or change the order type.
            order.order_status = 'rejected'
            order.save()

            message = 'Offer rejected successfully.'
            notification_type = 'client_offer_rejected'
            notification_title = 'Your Direct Offer Was Rejected'
            notification_message = f'Technician {technician_user.get_full_name()} has rejected your direct offer for order #{order.order_id}. Reason: {rejection_reason}'

        # Send notification to the client
        try:
            create_notification( # Using the helper function
                user=order.client_user,
                notification_type=notification_type,
                title=notification_title,
                message=notification_message,
                related_order=order,
                related_offer=offer # Pass the related offer
            )
        except Exception as e:
            print(f"Error sending notification for client offer response: {e}")

        response_data = {
            'message': message,
            'offer': ProjectOfferSerializer(offer, context={'request': request}).data,
        }
        if action_type == 'accept':
            response_data['order_status'] = order.order_status
        return Response(response_data, status=200)


class PublicUserViewSet(UserViewSet):
    """
    Public API endpoint to list users (for directory/search).
    """
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        return [permissions.AllowAny()]
