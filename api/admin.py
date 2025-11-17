from django.contrib import admin
from .models import (
    Review, IssueReport, Transaction
)
admin.site.register(Review)
admin.site.register(IssueReport)
admin.site.register(Transaction)
