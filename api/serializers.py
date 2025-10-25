from rest_framework import serializers
from .models.users import User, UserType
from .models.services import ServiceCategory, Service
from .models.technicians import TechnicianAvailability, TechnicianSkill, VerificationDocument
from .models.orders.core import Order

class UserTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserType
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True, 'required': False}}
        read_only_fields = ('groups', 'user_permissions', 'is_staff', 'is_superuser', 'is_active', 'last_login')

    def create(self, validated_data):
        # Remove fields that are not directly set during user creation or are many-to-many
        validated_data.pop('groups', None)
        validated_data.pop('user_permissions', None)
        validated_data.pop('is_staff', None)
        validated_data.pop('is_superuser', None)
        validated_data.pop('is_active', None)
        validated_data.pop('last_login', None)

        # Handle phone_number to ensure it's None if empty, to avoid unique constraint violation
        phone_number = validated_data.get('phone_number')
        if phone_number == '':
            validated_data['phone_number'] = None

        # Handle username to ensure it's None if empty, to avoid unique constraint violation
        username = validated_data.get('username')
        if username == '':
            validated_data['username'] = None

        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        # Remove password from validated_data if it's not being updated
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class TechnicianAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicianAvailability
        fields = '__all__'

class TechnicianSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicianSkill
        fields = '__all__'

class VerificationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationDocument
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
