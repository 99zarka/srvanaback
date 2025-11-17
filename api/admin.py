from django.contrib import admin
from .models import (
    Review, TechnicianAvailability, TechnicianSkill,
    VerificationDocument, Address, Conversation, Message, IssueReport,
    NotificationPreference, Notification, PaymentMethod, Transaction
)
admin.site.register(Review)
admin.site.register(TechnicianAvailability)
admin.site.register(TechnicianSkill)
admin.site.register(VerificationDocument)
admin.site.register(Address)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(IssueReport)
admin.site.register(NotificationPreference)
admin.site.register(Notification)
admin.site.register(PaymentMethod)
admin.site.register(Transaction)
