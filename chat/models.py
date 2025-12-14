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
