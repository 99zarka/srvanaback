from django.contrib import admin
from .models import (
    ServiceCategory, Service, Order, Payment, Review,
    TechnicianAvailability, TechnicianSkill, ProjectOffer, Complaint, Media,
    VerificationDocument, Address, Conversation, Message, IssueReport,
    NotificationPreference, Notification, PaymentMethod, Transaction
)

admin.site.register(ServiceCategory)
admin.site.register(Service)
admin.site.register(Order)
admin.site.register(Payment)
admin.site.register(Review)
admin.site.register(TechnicianAvailability)
admin.site.register(TechnicianSkill)
admin.site.register(ProjectOffer)
admin.site.register(Complaint)
admin.site.register(Media)
admin.site.register(VerificationDocument)
admin.site.register(Address)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(IssueReport)
admin.site.register(NotificationPreference)
admin.site.register(Notification)
admin.site.register(PaymentMethod)
admin.site.register(Transaction)
