from rest_framework import serializers
from ..models.transactions import Transaction
from orders.models import Order # Import Order for PrimaryKeyRelatedField queryset

class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(), required=False)
    transaction_type = serializers.ChoiceField(choices=Transaction.TRANSACTION_TYPE_CHOICES, required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    status = serializers.ChoiceField(choices=Transaction.STATUS_CHOICES, required=False)

    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('user',) # user is set by perform_create

    def validate(self, data):
        request = self.context.get('request')
        if request and request.method in ['PUT', 'PATCH']:
            # For updates, only 'status' can be modified by non-admin users
            if request.user and not request.user.user_type.user_type_name == 'admin':
                # Ensure that only 'status' is being updated
                for field_name in data:
                    if field_name not in ['status']:
                        raise serializers.ValidationError({field_name: "Only 'status' can be updated by non-admin users."})
        return data
