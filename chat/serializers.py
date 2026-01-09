import json
import re
from rest_framework import serializers
from .models import Conversation, Message, AIConversationMessage
from users.serializers.user_serializers import PublicUserSerializer
from filesupload.serializers.fields import CloudinaryFileField

class AIConversationMessageSerializer(serializers.ModelSerializer):
    # Add parsed content fields using our enhanced functions
    parsed_content = serializers.SerializerMethodField()
    reply = serializers.SerializerMethodField()
    is_irrelevant = serializers.SerializerMethodField()
    project_data = serializers.SerializerMethodField()
    offer_data = serializers.SerializerMethodField()
    technician_recommendations = serializers.SerializerMethodField()
    show_post_project = serializers.SerializerMethodField()
    show_direct_hire = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = AIConversationMessage
        fields = [
            'id', 'conversation', 'role', 'content', 'image_url', 'file_url', 'timestamp',
            'parsed_content', 'reply', 'is_irrelevant', 'project_data', 'offer_data',
            'technician_recommendations', 'show_post_project', 'show_direct_hire', 'can_edit'
        ]

    def get_parsed_content(self, obj):
        """Parse JSON from message content using enhanced functions and return structured data."""
        # Import our enhanced JSON parsing functions locally to avoid circular imports
        from ai.generate_proposal_view import extract_json_from_response, validate_and_normalize_response
        
        if obj.role == 'assistant' and obj.content and isinstance(obj.content, str):
            try:
                # Use our enhanced JSON extraction function
                extracted_json = extract_json_from_response(obj.content)
                # Use our enhanced validation and normalization function
                parsed_data = validate_and_normalize_response(extracted_json, obj.content)
                return parsed_data
            except Exception:
                # Fallback to basic parsing if enhanced functions fail
                try:
                    json_match = re.search(r'\{[\s\S]*\}', obj.content)
                    if json_match:
                        parsed = json.loads(json_match.group(0))
                        return validate_and_normalize_response(parsed, obj.content)
                except (json.JSONDecodeError, KeyError):
                    pass
        
        # Return minimal valid structure for non-assistant messages or parsing failures
        return {
            "reply": obj.content if obj.content else "",
            "is_irrelevant": False,
            "project_data": None,
            "offer_data": None,
            "technician_recommendations": [],
            "show_post_project": False,
            "show_direct_hire": False,
            "can_edit": False
        }

    def get_reply(self, obj):
        """Extract just the reply field from parsed content."""
        parsed = self.get_parsed_content(obj)
        return parsed.get('reply', obj.content if obj.content else "")

    def get_is_irrelevant(self, obj):
        """Extract the is_irrelevant field from parsed content."""
        parsed = self.get_parsed_content(obj)
        return parsed.get('is_irrelevant', False)

    def get_project_data(self, obj):
        """Extract the project_data field from parsed content."""
        parsed = self.get_parsed_content(obj)
        return parsed.get('project_data', None)

    def get_offer_data(self, obj):
        """Extract the offer_data field from parsed content."""
        parsed = self.get_parsed_content(obj)
        return parsed.get('offer_data', None)

    def get_technician_recommendations(self, obj):
        """Extract the technician_recommendations field from parsed content."""
        parsed = self.get_parsed_content(obj)
        return parsed.get('technician_recommendations', [])

    def get_show_post_project(self, obj):
        """Extract the show_post_project field from parsed content."""
        parsed = self.get_parsed_content(obj)
        return parsed.get('show_post_project', False)

    def get_show_direct_hire(self, obj):
        """Extract the show_direct_hire field from parsed content."""
        parsed = self.get_parsed_content(obj)
        return parsed.get('show_direct_hire', False)

    def get_can_edit(self, obj):
        """Extract the can_edit field from parsed content."""
        parsed = self.get_parsed_content(obj)
        return parsed.get('can_edit', False)

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
