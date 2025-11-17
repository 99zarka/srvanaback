from django.contrib import admin
from .models import (
    Review, Address, IssueReport,
    NotificationPreference, Notification, PaymentMethod, Transaction
)
admin.site.register(Review)
admin.site.register(Address)
admin.site.register(IssueReport)
admin.site.register(NotificationPreference)
admin.site.register(Notification)
admin.site.register(PaymentMethod)
admin.site.register(Transaction)
