from rest_framework import serializers
from .models.users import User, UserType
from .models.services import ServiceCategory, Service
from .models.technicians import TechnicianAvailability, TechnicianSkill, VerificationDocument
from .models.orders.core import Order
from .models.orders.feedback import ProjectOffer
from .models.addresses import Address
from .models.payment_methods import PaymentMethod
from .models.notifications import NotificationPreference, Notification
from .models.reviews import Review
from .models.issue_reports import IssueReport
from .models.transactions import Transaction
from .models.chat import Conversation, Message

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

class ProjectOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectOffer
        fields = '__all__'

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = '__all__'

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = NotificationPreference
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = Notification
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    reviewer = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    technician = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())

    class Meta:
        model = Review
        fields = '__all__'

class IssueReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueReport
        fields = '__all__'

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

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
