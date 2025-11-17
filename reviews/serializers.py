from rest_framework import serializers
from .models import Review
from users.models import User
from orders.models import Order

class ReviewSerializer(serializers.ModelSerializer):
    reviewer = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    technician = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())

    class Meta:
        model = Review
        fields = '__all__'
