from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from api.permissions import IsAdminUser, IsConversationParticipantOrAdmin, IsMessageSenderOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin

class ConversationViewSet(OwnerFilteredQuerysetMixin, viewsets.ModelViewSet):
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
