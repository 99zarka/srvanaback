from rest_framework import serializers
from .models import Dispute
from users.serializers import UserSerializer # Assuming UserSerializer exists

class DisputeSerializer(serializers.ModelSerializer):
    client_user = UserSerializer(read_only=True)
    technician_user = UserSerializer(read_only=True)
    admin_reviewer = UserSerializer(read_only=True)

    class Meta:
        model = Dispute
        fields = '__all__'
        read_only_fields = ('dispute_id', 'initiated_date', 'status', 'admin_reviewer', 'resolution_date', 'resolved_amount_to_client', 'resolved_amount_to_technician')
