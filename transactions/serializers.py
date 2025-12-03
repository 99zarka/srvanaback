from rest_framework import serializers
from .models import Transaction
from orders.models import Order
from users.models import User # Import User for PrimaryKeyRelatedField queryset
from disputes.models import Dispute # Import Dispute for PrimaryKeyRelatedField queryset

class TransactionSerializer(serializers.ModelSerializer):
    source_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    destination_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(), required=False, allow_null=True)
    dispute = serializers.PrimaryKeyRelatedField(queryset=Dispute.objects.all(), required=False, allow_null=True)
    transaction_type = serializers.ChoiceField(choices=Transaction.TRANSACTION_TYPE_CHOICES)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.CharField(max_length=255, required=False, allow_blank=True)
    transaction_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    timestamp = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('timestamp',)

    def validate(self, data):
        # No specific validation needed here, as status is removed and fields are handled by permissions/views.
        return data
