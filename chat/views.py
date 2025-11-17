from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from api.permissions import IsAdminUser, IsConversationParticipantOrAdmin, IsMessageSenderOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin

class ConversationViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Conversations to be viewed or edited.

    list:
    Return a list of conversations the authenticated user is a participant in.
    Permissions: Authenticated User (participant) or Admin User.
    Usage: GET /api/chat/conversations/

    retrieve:
    Return a specific conversation by ID.
    Permissions: Authenticated User (participant) or Admin User.
    Usage: GET /api/chat/conversations/{id}/

    create:
    Create a new conversation. The authenticated user must be included in the participants.
    Permissions: Authenticated User or Admin User.
    Usage: POST /api/chat/conversations/
    Body: {"participants": [1, 2], "topic": "Service Inquiry"}

    update:
    Update an existing conversation.
    Permissions: Authenticated User (participant) or Admin User.
    Usage: PUT /api/chat/conversations/{id}/
    Body: {"topic": "Updated Service Inquiry"}

    partial_update:
    Partially update an existing conversation.
    Permissions: Authenticated User (participant) or Admin User.
    Usage: PATCH /api/chat/conversations/{id}/
    Body: {"topic": "New Topic"}

    destroy:
    Delete a conversation.
    Permissions: Authenticated User (participant) or Admin User.
    Usage: DELETE /api/chat/conversations/{id}/
    """
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsConversationParticipantOrAdmin)]

    def get_filtered_queryset(self, user, base_queryset):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return base_queryset # Rely on object-level permissions
        return base_queryset.filter(participants=user)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create conversations.")
        
        participants_data = self.request.data.get('participants')
        if user.user_type.user_type_name != 'admin':
            if not participants_data or user.user_id not in participants_data:
                raise serializers.ValidationError({"participants": "The authenticated user must be a participant in the conversation."})
        
        serializer.save()

class MessageViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Messages to be viewed or edited.

    list:
    Return a list of messages for conversations the authenticated user is a participant in.
    Permissions: Authenticated User (participant in conversation) or Admin User.
    Usage: GET /api/chat/messages/

    retrieve:
    Return a specific message by ID.
    Permissions: Authenticated User (participant in conversation) or Admin User.
    Usage: GET /api/chat/messages/{id}/

    create:
    Create a new message within a conversation. The authenticated user must be a participant in the conversation.
    Permissions: Authenticated User (participant in conversation) or Admin User.
    Usage: POST /api/chat/messages/
    Body: {"conversation": 1, "content": "Hello there!"}

    update:
    Update an existing message.
    Permissions: Authenticated User (sender) or Admin User.
    Usage: PUT /api/chat/messages/{id}/
    Body: {"content": "Updated message content."}

    partial_update:
    Partially update an existing message.
    Permissions: Authenticated User (sender) or Admin User.
    Usage: PATCH /api/chat/messages/{id}/
    Body: {"content": "Partial update."}

    destroy:
    Delete a message.
    Permissions: Authenticated User (sender) or Admin User.
    Usage: DELETE /api/chat/messages/{id}/
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsMessageSenderOrAdmin)]
        else: # list, retrieve, create
            self.permission_classes = [IsAdminUser | (permissions.IsAuthenticated & IsConversationParticipantOrAdmin)]
        return super().get_permissions()

    def get_filtered_queryset(self, user, base_queryset):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return base_queryset # Rely on object-level permissions
        return base_queryset.filter(conversation__participants=user)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create messages.")
        
        conversation_id = self.request.data.get('conversation')
        if not conversation_id:
            raise serializers.ValidationError({"conversation": "This field is required."})
        
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            raise serializers.ValidationError({"conversation": "Conversation does not exist."})
        
        if user.user_type.user_type_name != 'admin' and user not in conversation.participants.all():
            raise PermissionDenied("You are not a participant in this conversation.")
        
        serializer.save(sender=user, conversation=conversation)
