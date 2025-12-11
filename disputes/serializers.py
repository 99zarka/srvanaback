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

    class Meta:
        model = Dispute
        fields = '__all__'
        read_only_fields = ('dispute_id', 'created_at', 'status', 'resolution_date')
