from rest_framework import serializers
from .models import Review
from users.models import User
from orders.models import Order

class ReviewSerializer(serializers.ModelSerializer):
    reviewer = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    technician = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    order = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = '__all__'
        extra_kwargs = {
            'reviewer': {'required': False, 'allow_null': True}
        }

    def get_order(self, obj):
        """Return serialized order data including client information"""
        if obj.order:
            from orders.serializers import OrderSerializer
            return OrderSerializer(obj.order, context=self.context).data
        return None

    def to_internal_value(self, data):
        # If reviewer is not provided, add the authenticated user as reviewer
        request = self.context.get('request')
        if request and request.method == 'POST' and 'reviewer' not in data:
            data = data.copy()
            data['reviewer'] = str(request.user.user_id)
        return super().to_internal_value(data)


class PublicReviewSerializer(serializers.ModelSerializer):
    """
    A simplified serializer for reviews intended for public consumption.
    Excludes sensitive information like reviewer details.
    """
    class Meta:
        model = Review
        fields = [
            'rating',
            'comment', 
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields
