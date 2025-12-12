from rest_framework import serializers
from services.models import ServiceCategory, Service
from filesupload.serializers.fields import CloudinaryImageField

class ServiceCategorySerializer(serializers.ModelSerializer):
    icon_url = CloudinaryImageField(required=False, allow_null=True)

    class Meta:
        model = ServiceCategory
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    # Remove the read_only=True to allow writing the category ID
    # The category field will accept the category ID directly
    category = ServiceCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.all(), 
        source='category', 
        write_only=True,
        required=True
    )

    class Meta:
        model = Service
        fields = '__all__'
