from rest_framework import serializers
from ..models.notifications import NotificationPreference, Notification
from users.models import User # Import User for PrimaryKeyRelatedField queryset

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
