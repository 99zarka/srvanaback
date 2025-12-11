from rest_framework import serializers
from .models import Dispute
from users.serializers.user_serializers import PublicUserSerializer

class DisputeSerializer(serializers.ModelSerializer):
    initiator = PublicUserSerializer(read_only=True)

    class Meta:
        model = Dispute
        fields = '__all__'
        read_only_fields = ('dispute_id', 'created_at', 'status', 'resolution_date')
