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

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password2', 'first_name', 'last_name', 'phone_number', 'address', 'user_type')
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone_number': {'required': False},
            'address': {'required': False},
            'user_type': {'required': False}, # Make user_type optional in serializer
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        # user_type is now handled by the model's default, so we remove it from validated_data if present
        if 'user_type' in validated_data:
            validated_data.pop('user_type')

        # Convert empty string phone_number to None to allow unique=True with multiple NULLs
        phone_number = validated_data.get('phone_number')
        if phone_number == '':
            validated_data['phone_number'] = None

        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data.get('username'),
            first_name=validated_data.get('first_name', ''), # Provide default empty string for optional fields
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number'), # Use the potentially modified phone_number
            address=validated_data.get('address', ''),
            # user_type will now be set by the model's default
            password=validated_data['password']
        )
        return user

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
