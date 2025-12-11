from rest_framework import serializers
from .models import Order, ProjectOffer
from datetime import date
from users.models import User
from users.serializers.user_serializers import PublicUserSerializer, UserTypeSerializer
from services.models import Service
from services.serializers import ServiceSerializer
from disputes.serializers import DisputeSerializer
from rest_framework.exceptions import ValidationError

class NestedOrderSerializer(serializers.ModelSerializer):
    client_user = PublicUserSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = Order
        fields = '__all__'

class ProjectOfferDetailSerializer(serializers.ModelSerializer):
    technician_user = PublicUserSerializer(read_only=True) # Assuming PublicUserSerializer is sufficient for technician details

    class Meta:
        model = ProjectOffer
        fields = ['offer_id', 'offered_price', 'offer_description', 'offer_date', 'status', 'technician_user']

class PublicOrderSerializer(serializers.ModelSerializer):
    client_user = PublicUserSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'order_id', 'service', 'client_user', 'problem_description',
            'requested_location', 'scheduled_date', 'scheduled_time_start',
            'scheduled_time_end', 'order_type', 'creation_timestamp', 'order_status',
            'expected_price'
        ]
        read_only_fields = fields # All fields are read-only for public view

class ServiceField(serializers.Field):
    """
    Custom field that handles both input (service_id) and output (full service details)
    """
    def to_representation(self, value):
        # For output: show full service details using ServiceSerializer
        if value is None:
            return None
        return ServiceSerializer(value).data

    def to_internal_value(self, data):
        # For input: accept service_id and return the Service instance
        if isinstance(data, int) or (isinstance(data, str) and data.isdigit()):
            try:
                return Service.objects.get(pk=int(data))
            except Service.DoesNotExist:
                raise serializers.ValidationError(f"Service with id {data} does not exist.")
        elif isinstance(data, dict) and 'service_id' in data:
            # Handle the case where frontend sends {'service_id': 34}
            service_id = data['service_id']
            try:
                return Service.objects.get(pk=service_id)
            except Service.DoesNotExist:
                raise serializers.ValidationError(f"Service with id {service_id} does not exist.")
        else:
            raise serializers.ValidationError("Invalid service data. Expected service_id or service object.")

class OrderSerializer(serializers.ModelSerializer):
    client_user = PublicUserSerializer(read_only=True)
    service = ServiceField()  # Use custom field that handles both input and output
    associated_offer = serializers.SerializerMethodField()
    project_offers = ProjectOfferDetailSerializer(many=True, read_only=True) # Added to display all offers
    dispute = serializers.SerializerMethodField()

    # Define order_type as a CharField with choices for validation
    order_type = serializers.ChoiceField(choices=Order.ORDER_TYPE_CHOICES, required=True)

    # Explicitly define final_price as a writable field (not read_only)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    expected_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)

    def get_associated_offer(self, obj):
        # Get prefetched project offers to avoid additional queries
        if hasattr(obj, '_prefetched_objects_cache') and 'project_offers' in obj._prefetched_objects_cache:
            project_offers = obj._prefetched_objects_cache['project_offers']
        else:
            # Fallback to accessing the prefetched relation
            project_offers = obj.project_offers.all()
        
        # Convert to list once to avoid multiple iterations
        offers_list = list(project_offers)
        
        # Prioritize an accepted offer regardless of order_type
        accepted_offer = next((offer for offer in offers_list if offer.status == 'accepted'), None)
        if accepted_offer:
            return ProjectOfferDetailSerializer(accepted_offer).data

        # If no accepted offer, consider other types based on order_type
        if obj.order_type == 'direct_hire':
            # For direct hire, prioritize a client-initiated direct offer if no accepted offer
            client_offer = next((offer for offer in offers_list if offer.offer_initiator == 'client' and offer.status == 'pending'), None)
            if client_offer:
                return ProjectOfferDetailSerializer(client_offer).data
        elif obj.order_type == 'service_request':
            # For service request, prioritize any pending technician offer if no accepted offer
            technician_pending_offer = next((offer for offer in offers_list if offer.offer_initiator == 'technician' and offer.status == 'pending'), None)
            if technician_pending_offer:
                return ProjectOfferDetailSerializer(technician_pending_offer).data

        return None # No associated offer found based on criteria

    def get_dispute(self, obj):
        # Get the most recent dispute for this order using prefetched data
        # Check if disputes are prefetched in the _prefetched_objects_cache
        if hasattr(obj, '_prefetched_objects_cache') and 'disputes' in obj._prefetched_objects_cache:
            disputes = obj._prefetched_objects_cache['disputes']
            if disputes:
                # Find the most recent dispute from prefetched data
                most_recent = max(disputes, key=lambda d: d.created_at)
                return DisputeSerializer(most_recent).data
        else:
            # Fallback to database query if not prefetched (shouldn't happen with our optimization)
            dispute = obj.disputes.order_by('-created_at').first()
            if dispute:
                return DisputeSerializer(dispute).data
        return None

    def to_internal_value(self, data):
        # Handle service_id -> service field mapping for nested cases
        if 'service_id' in data and 'service' not in data:
            data['service'] = data.pop('service_id')
        return super().to_internal_value(data)

    # Removed to_representation method as service is now directly serialized

    class Meta:
        model = Order
        fields = [
            'order_id', 'service', 'client_user', 'problem_description',
            'requested_location', 'scheduled_date', 'scheduled_time_start',
            'scheduled_time_end', 'order_type', 'creation_timestamp', 'order_status',
            'technician_user', 'associated_offer', 'project_offers', 'dispute', 'final_price', 'expected_price'
        ]
        read_only_fields = ['order_id', 'creation_timestamp', 'order_status', 'technician_user'] # Removed 'order_type'

class ProjectOfferSerializer(serializers.ModelSerializer):
    technician_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(user_type__user_type_name='technician'))
    offer_initiator = serializers.CharField(read_only=True)
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())

    class Meta:
        model = ProjectOffer
        fields = '__all__'
        read_only_fields = ['offer_id', 'offer_date', 'status']

class ClientMakeOfferSerializer(serializers.ModelSerializer):
    technician_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(user_type__user_type_name='technician'), write_only=True, required=True)
    order = OrderSerializer(required=True)
    client_agreed_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True, allow_null=False) # Renamed final_price to client_agreed_price

    class Meta:
        model = ProjectOffer
        fields = [
            'order',
            'technician_user',
            'offer_description',
            'client_agreed_price', # Added client_agreed_price to fields
        ]
        extra_kwargs = {
            'offered_price': {'required': False, 'allow_null': True}, # Make offered_price not required for client offers
            'offer_description': {'required': False, 'allow_null': True},
            # Removed final_price from extra_kwargs as it's now client_agreed_price and handled explicitly
        }
        read_only_fields = ['offer_id', 'offer_date', 'status', 'offer_initiator']

    def create(self, validated_data):
        order_data = validated_data.pop('order')
        technician_user = validated_data.pop('technician_user')
        client_agreed_price = validated_data.pop('client_agreed_price') # Pop client_agreed_price from validated_data

        request = self.context.get('request', None)
        if not request or not request.user.is_authenticated:
            raise ValidationError("Authentication required to create an offer.")

        client_user = request.user

        if 'service' in order_data and isinstance(order_data['service'], Service):
            order_data['service'] = order_data['service'].pk

        # Ensure order_type is set for the order being created
        order_data['order_type'] = 'direct_hire' # ClientMakeOfferSerializer specifically creates direct_hire orders
        order_data['creation_timestamp'] = date.today()
        order_data['order_status'] = 'AWAITING_TECHNICIAN_RESPONSE'

        # Set final_price in order_data using client_agreed_price
        order_data['final_price'] = client_agreed_price

        order_serializer = OrderSerializer(data=order_data, context=self.context)
        order_serializer.is_valid(raise_exception=True)
        order = order_serializer.save(client_user=client_user) # Pass client_user directly to save()

        offer = ProjectOffer.objects.create(
            order=order,
            technician_user=technician_user,
            offer_initiator='client',
            offer_date=date.today(),
            status='pending',
            offered_price=client_agreed_price, # Set offered_price from client_agreed_price
            offer_description=validated_data.pop('offer_description', None) # Pop offer_description if present
        )
        return offer
