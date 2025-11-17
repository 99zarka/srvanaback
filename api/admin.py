from django.contrib import admin
from .models import (
    IssueReport, Transaction
)
admin.site.register(IssueReport)
admin.site.register(Transaction)
