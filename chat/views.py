from rest_framework import viewsets, permissions, pagination
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Prefetch, Count
from django.core.paginator import Paginator
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from api.permissions import IsAdminUser, IsConversationParticipantOrAdmin, IsMessageSenderOrAdmin
from api.mixins import OwnerFilteredQuerysetMixin

class DynamicPageSizePagination(pagination.PageNumberPagination):
    """
    Custom pagination class that respects the page_size parameter from the URL.
    Falls back to a default page size if not specified.
    """
    page_size_query_param = 'page_size'
    max_page_size = 100

class ConversationViewSet(viewsets.ModelViewSet):
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
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated & IsConversationParticipantOrAdmin]
    pagination_class = DynamicPageSizePagination

    def get_queryset(self):
        user = self.request.user
        queryset = Conversation.objects.prefetch_related(
            'participants__user_type',
            Prefetch(
                'messages',
                queryset=Message.objects.select_related('sender').order_by('-timestamp')[:1],
                to_attr='prefetched_last_message'
            )
        ).annotate(
            message_count=Count('messages')
        ).order_by('-updated_at')
        
        # Apply filtering for list action - only show conversations user participates in
        if self.action == 'list':
            return queryset.filter(participants=user, message_count__gt=0)
        return queryset

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def messages(self, request, pk=None):
        """
        Get paginated messages for a conversation
        Usage: GET /api/chat/conversations/{id}/messages/?page=1&limit=50
        """
        conversation = self.get_object()
        user = request.user
        
        # Verify user is participant
        if user.user_type.user_type_name != 'admin' and user not in conversation.participants.all():
            raise PermissionDenied("You are not a participant in this conversation.")
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        limit = min(int(request.query_params.get('limit', 50)), 100)  # Max 100 per page
        
        messages = Message.objects.filter(conversation=conversation).select_related(
            'sender', 'sender__user_type'
        ).order_by('-timestamp')  # Changed from '-timestamp' to 'timestamp' for chronological order
        
        paginator = Paginator(messages, limit)
        messages_page = paginator.get_page(page)
        
        serializer = MessageSerializer(messages_page, many=True, context={'request': request})
        
        return Response({
            'messages': serializer.data,
            'pagination': {
                'current_page': page,
                'total_pages': paginator.num_pages,
                'total_messages': paginator.count,
                'has_next': messages_page.has_next(),
                'has_previous': messages_page.has_previous(),
            }
        })

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated], url_path='get-with-user/(?P<user_id>[^/.]+)')
    def get_with_user(self, request, user_id=None):
        """
        Get or create conversation with a specific user
        Usage: GET /api/chat/conversations/get-with-user/{user_id}/
        """
        from users.models import User
        current_user = request.user
        target_user_id = user_id  # Now user_id comes from the URL path parameter
        
        if not target_user_id:
            return Response({'error': 'User ID is required'}, status=400)
        
        if current_user.user_id == int(target_user_id):
            return Response({'error': 'Cannot create conversation with yourself'}, status=400)
        
        try:
            target_user = User.objects.get(user_id=target_user_id)
        except User.DoesNotExist:
            return Response({'error': 'Target user not found'}, status=404)
        
        # Find existing conversation with these two users
        conversations = Conversation.objects.filter(
            participants=current_user
        ).filter(
            participants=target_user
        ).filter(
            participants__in=[current_user, target_user]
        ).distinct()
        
        conversation = None
        for conv in conversations:
            if set(conv.participants.values_list('user_id', flat=True)) == {current_user.user_id, target_user.user_id}:
                conversation = conv
                break
        
        if not conversation:
            # Create new conversation with two participants
            conversation = Conversation.objects.create()
            conversation.participants.add(current_user, target_user)
            conversation.save()
        
        serializer = ConversationSerializer(conversation, context={'request': request})
        return Response(serializer.data)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create conversations.")
        
        participants_data = self.request.data.get('participants')
        if user.user_type.user_type_name != 'admin':
            if not participants_data or user.user_id not in participants_data:
                raise serializers.ValidationError({"participants": "The authenticated user must be a participant in the conversation."})
        
        serializer.save()

class MessageViewSet(viewsets.ModelViewSet):
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
    serializer_class = MessageSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Message.objects.select_related(
            'sender', 'sender__user_type', 'conversation'
        ).prefetch_related(
            'sender__user_type'
        ).order_by('-timestamp')
        
        # Apply filtering for list action - only show messages from conversations user participates in
        if self.action == 'list':
            return queryset.filter(conversation__participants=user)
        return queryset
    

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated & IsMessageSenderOrAdmin]
        else: # list, retrieve, create
            self.permission_classes = [permissions.IsAuthenticated & IsConversationParticipantOrAdmin]
        return super().get_permissions()

    def get_filtered_queryset(self, user, base_queryset):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return base_queryset # Rely on object-level permissions
        # Both admin and non-admin users should only see messages from conversations they participate in
        return base_queryset.filter(conversation__participants=user)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to create messages.")
        
        conversation_id = self.request.data.get('conversation')
        if not conversation_id:
            raise serializers.ValidationError({"conversation": "This field is required."})
        
        try:
            conversation = Conversation.objects.prefetch_related('participants').get(id=conversation_id)
        except Conversation.DoesNotExist:
            raise serializers.ValidationError({"conversation": "Conversation does not exist."})
        
        if user.user_type.user_type_name != 'admin' and user not in conversation.participants.all():
            raise PermissionDenied("You are not a participant in this conversation.")
        
        serializer.save(sender=user, conversation=conversation)
