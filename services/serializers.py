from rest_framework import serializers
from services.models import ServiceCategory, Service
from filesupload.serializers.fields import CloudinaryImageField

class ServiceCategorySerializer(serializers.ModelSerializer):
    icon_url = CloudinaryImageField(required=False, allow_null=True)

    class Meta:
        model = ServiceCategory
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    # Handle category as both readable and writable
    category = ServiceCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.all(), 
        source='category', 
        write_only=True,
        required=False  # Make it not required initially to handle both cases
    )

    class Meta:
        model = Service
        fields = '__all__'

    def to_internal_value(self, data):
        # Handle the case where 'category' is sent as an ID (for backward compatibility)
        if 'category' in data and isinstance(data['category'], int):
            data = data.copy()  # Don't modify original data
            data['category_id'] = data.pop('category')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        # Ensure category is properly serialized with select_related optimization
        return super().to_representation(instance)
