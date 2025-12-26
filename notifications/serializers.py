from rest_framework import serializers
from .models import NotificationPreference, Notification
from .utils import get_notification_frontend_url
from users.models import User # Import User for PrimaryKeyRelatedField queryset

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = NotificationPreference
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    frontend_url = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = '__all__'

    def get_frontend_url(self, obj):
        """
        Get the frontend URL for this notification.
        """
        return get_notification_frontend_url(obj)
