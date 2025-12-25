from rest_framework import serializers
from .models import Dispute, DisputeResponse
from users.serializers.user_serializers import PublicUserSerializer
from filesupload.serializers.fields import CloudinaryFileField

class DisputeResponseSerializer(serializers.ModelSerializer):
    sender = PublicUserSerializer(read_only=True)
    file_url = CloudinaryFileField(required=False)  # Make file upload optional

    class Meta:
        model = DisputeResponse
        fields = '__all__'
        read_only_fields = ('id', 'dispute', 'sender', 'created_at')

class DisputeSerializer(serializers.ModelSerializer):
    initiator = PublicUserSerializer(read_only=True)
    responses = DisputeResponseSerializer(many=True, read_only=True)
    # Add technician user from the associated order
    technician_user = serializers.SerializerMethodField()
    # Add client user from the associated order (in case it's different from initiator)
    client_user = serializers.SerializerMethodField()

    class Meta:
        model = Dispute
        fields = '__all__'
        read_only_fields = ('dispute_id', 'created_at', 'status', 'resolution_date')

    def get_technician_user(self, obj):
        """Get technician user from the associated order"""
        if obj.order and obj.order.technician_user:
            return PublicUserSerializer(obj.order.technician_user).data
        return None

    def get_client_user(self, obj):
        """Get client user from the associated order"""
        if obj.order and obj.order.client_user:
            return PublicUserSerializer(obj.order.client_user).data
        return None
