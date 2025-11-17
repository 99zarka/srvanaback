from rest_framework import serializers
from services.models import ServiceCategory, Service
from filesupload.serializers.fields import CloudinaryImageField

class ServiceCategorySerializer(serializers.ModelSerializer):
    icon_url = CloudinaryImageField(required=False, allow_null=True)

    class Meta:
        model = ServiceCategory
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'
