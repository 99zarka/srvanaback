from django.contrib import admin
from .models import Conversation, Message, AIConversation, AIConversationMessage

admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(AIConversation)
admin.site.register(AIConversationMessage)
