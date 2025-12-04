from rest_framework import serializers
from rest_framework import serializers
from .models import Order, ProjectOffer
from datetime import date
from users.models import User # Import User model

from users.serializers.user_serializers import PublicUserSerializer, UserTypeSerializer
from services.models import Service # Import Service model
from services.serializers import ServiceSerializer # Import ServiceSerializer

class NestedOrderSerializer(serializers.ModelSerializer):
    client_user = PublicUserSerializer(read_only=True) # Nest client user details
    service = ServiceSerializer(read_only=True) # Nest service details

    class Meta:
        model = Order
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    client_user = PublicUserSerializer(read_only=True) # Also include for the main OrderSerializer if used elsewhere
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all()) # Accept service ID for creation


    class Meta:
        model = Order
        fields = '__all__'

class ProjectOfferSerializer(serializers.ModelSerializer):
    technician_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(user_type__user_type_name='technician')) # Accept technician user ID for creation
    offer_initiator = serializers.CharField(read_only=True) # Read-only for creation, set by view
    order = NestedOrderSerializer() # Nest order details, including service, for detailed representation

    class Meta:
        model = ProjectOffer
        fields = '__all__'
        read_only_fields = ['offer_id', 'offer_date', 'status']

class ClientMakeOfferSerializer(serializers.ModelSerializer):
    # This serializer is for clients to make offers to technicians.
    # It requires order details to create an order first, or link to an existing one.
    # It will also require the target technician_user_id.
    
    # We will accept a technician_user_id for validation purposes
    technician_user_id = serializers.IntegerField(write_only=True, required=True)
    
    class Meta:
        model = ProjectOffer
        fields = [
            'order', # Can be an existing order or will be created
            'technician_user_id',
            'offered_price',
            'offer_description',
        ]
        extra_kwargs = {
            'order': {'required': False}, # Order can be created by the view if not provided
            'offered_price': {'required': True},
            'offer_description': {'required': False},
        }
        read_only_fields = ['offer_id', 'offer_date', 'status', 'technician_user', 'offer_initiator']
