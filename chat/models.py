from django.db import models
from users.models import User
from cloudinary.models import CloudinaryField

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        usernames = [user.username or f"User {user.user_id}" for user in self.participants.all()]
        return f"Conversation {self.id} with {', '.join(usernames)}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(blank=True)  # Text content (optional for file-only messages)
    file_url = CloudinaryField('chat_files', null=True, blank=True)  # Cloudinary file uploads
    file_type = models.CharField(max_length=20, blank=True)  # 'image', 'document', 'video', etc.
    file_name = models.CharField(max_length=255, blank=True) # Original filename
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        db_table = 'MESSAGE'
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['sender']),
            models.Index(fields=['conversation', 'is_read']),
        ]

    def __str__(self):
        return f"Message from {self.sender.username} in Conversation {self.conversation.id} at {self.timestamp}"

class AIConversation(models.Model):
    """Represents a conversation thread with the AI assistant."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        if self.user:
            return f"AI Conversation {self.id} for {self.user.username}"
        return f"AI Conversation {self.id} for Anonymous User"

    def discard(self):
        """Marks the conversation as inactive."""
        self.is_active = False
        self.save()

    def get_history(self):
        """Returns the message history for use with the AI client."""
        return list(self.messages.values('role', 'content'))


class AIConversationMessage(models.Model):
    """Stores a single message (prompt or response) in an AI conversation."""
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
    )
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    image_url = CloudinaryField('chat_images', null=True, blank=True)
    file_url = CloudinaryField('chat_files', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.get_role_display()} message in AI Conversation {self.conversation.id} at {self.timestamp}"
