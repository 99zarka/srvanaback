from django.contrib import admin
from .models import (
    Review, IssueReport,
    NotificationPreference, Notification, PaymentMethod, Transaction
)
admin.site.register(Review)
admin.site.register(IssueReport)
admin.site.register(NotificationPreference)
admin.site.register(Notification)
admin.site.register(PaymentMethod)
admin.site.register(Transaction)
