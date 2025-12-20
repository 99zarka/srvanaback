from rest_framework import serializers
from .models import Conversation, Message, AIConversationMessage
from users.serializers.user_serializers import PublicUserSerializer
from filesupload.serializers.fields import CloudinaryFileField

class AIConversationMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIConversationMessage
        fields = ['id', 'conversation', 'role', 'content', 'image_url', 'file_url', 'timestamp']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Handle CloudinaryResource objects by converting to URL and fixing malformed URLs
        if instance.image_url:
            if hasattr(instance.image_url, 'url'):
                image_url = instance.image_url.url
            elif str(instance.image_url).startswith('http'):
                image_url = str(instance.image_url)
            else:
                image_url = str(instance.image_url)
            
            # Fix malformed URLs that have "image/upload/" prefix
            if image_url.startswith('image/upload/https://'):
                image_url = image_url.replace('image/upload/https://', 'https://')
            
            data['image_url'] = image_url
        
        if instance.file_url:
            if hasattr(instance.file_url, 'url'):
                file_url = instance.file_url.url
            elif str(instance.file_url).startswith('http'):
                file_url = str(instance.file_url)
            else:
                file_url = str(instance.file_url)
            
            data['file_url'] = file_url
        
        return data

class ConversationSerializer(serializers.ModelSerializer):
    participants_info = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()  # For conversation detail view
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'participants', 'participants_info', 'last_message', 
            'messages', 'created_at', 'updated_at'
        ]
    
    def get_participants_info(self, obj):
        # Use prefetch optimization
        participants = obj.participants.select_related('user_type').all()
        return [
            {
                'id': user.user_id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'profile_photo': user.profile_photo.url if (user.profile_photo and hasattr(user.profile_photo, 'url')) else None,
                'user_type': user.user_type.user_type_name if user.user_type else None,
                'is_online': getattr(user, 'is_online', False) # If online status tracking is added
            }
            for user in participants
        ]
    
    def get_last_message(self, obj):
        # Use prefetch to avoid N+1
        last_msg = obj.messages.select_related('sender').last()
        if last_msg:
            # Handle CloudinaryResource object by converting to URL
            file_url = None
            if last_msg.file_url:
                if hasattr(last_msg.file_url, 'url'):
                    file_url = last_msg.file_url.url
                elif str(last_msg.file_url).startswith('http'):
                    file_url = str(last_msg.file_url)
            
            return {
                'id': last_msg.id,
                'content': last_msg.content,
                'file_url': file_url,
                'file_type': last_msg.file_type,
                'sender_name': last_msg.sender.get_full_name(),
                'timestamp': last_msg.timestamp,
                'is_read': last_msg.is_read
            }
        return None
    
    def get_messages(self, obj):
        # For conversation detail view - limited messages
        messages = obj.messages.select_related('sender').order_by('-timestamp')[:50]
        return MessageSerializer(messages, many=True, context=self.context).data

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_avatar = serializers.SerializerMethodField()
    file_url = CloudinaryFileField(required=False)

    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'sender_name', 'sender_avatar',
            'content', 'file_url', 'file_type', 'file_name', 
            'timestamp', 'is_read', 'reply_to'
        ]
        read_only_fields = ('id', 'sender', 'timestamp')
    
    def get_sender_avatar(self, obj):
        return obj.sender.profile_photo.url if (obj.sender.profile_photo and hasattr(obj.sender.profile_photo, 'url')) else None
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Handle CloudinaryResource object by converting to URL
        if instance.file_url:
            if hasattr(instance.file_url, 'url'):
                data['file_url'] = instance.file_url.url
            elif str(instance.file_url).startswith('http'):
                data['file_url'] = str(instance.file_url)
        return data
