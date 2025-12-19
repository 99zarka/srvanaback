from rest_framework import serializers
from users.models import User, UserType
from filesupload.serializers.fields import CloudinaryImageField
from reviews.serializers import PublicReviewSerializer

class UserTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserType
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    profile_photo = CloudinaryImageField(required=False, allow_null=True)
    user_type = serializers.StringRelatedField(source='user_type.user_type_name') # Display user type name

    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True, 'required': False}}
        read_only_fields = ('groups', 'user_permissions', 'is_staff', 'is_superuser', 'is_active', 'last_login', 'available_balance', 'in_escrow_balance', 'pending_balance')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request', None)
        if request and request.user.is_authenticated and request.user.is_superuser:
            # Allow superusers to update balance fields
            for field_name in ['available_balance', 'in_escrow_balance', 'pending_balance']:
                if field_name in self.fields:
                    self.fields[field_name].read_only = False


class PublicUserSerializer(serializers.ModelSerializer):
    profile_photo = CloudinaryImageField(required=False, allow_null=True)
    user_type = serializers.StringRelatedField(source='user_type.user_type_name') # Display user type name
    overall_rating = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'user_id', 'first_name', 'last_name', 'username', 'bio', 'profile_photo', 'specialization',
            'user_type', 'overall_rating', 'num_jobs_completed', 'average_response_time', 'address',
            'registration_date', 'account_status', 'verification_status', 'access_level', 'reviews'
        )
        read_only_fields = fields # All fields are read-only for public view

    def get_reviews(self, obj):
        """Return reviews using PublicReviewSerializer"""
        reviews = obj.received_reviews.all()
        return PublicReviewSerializer(reviews, many=True, context=self.context).data

    def get_overall_rating(self, obj):
        # Ensure rating is returned as float, not string
        if obj.overall_rating is not None:
            return float(obj.overall_rating)
        return None


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password2', 'first_name', 'last_name', 'phone_number', 'address')
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone_number': {'required': False},
            'address': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')

        # Convert empty string phone_number to None to allow unique=True with multiple NULLs
        phone_number = validated_data.get('phone_number')
        if phone_number == '':
            validated_data['phone_number'] = None

        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data.get('username'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number'),
            address=validated_data.get('address', ''),
            password=validated_data['password']
        )
        return user
