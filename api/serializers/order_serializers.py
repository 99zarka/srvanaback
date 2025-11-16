from rest_framework import serializers
from ..models.orders.core import Order
from ..models.orders.feedback import ProjectOffer

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

class ProjectOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectOffer
        fields = '__all__'
