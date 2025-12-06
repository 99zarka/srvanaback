from django.contrib import admin
from .models import Dispute

@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ('dispute_id', 'order', 'initiator', 'status', 'created_at', 'resolution')
    list_filter = ('status', 'resolution', 'created_at')
    search_fields = ('dispute_id', 'order__order_id', 'initiator__username', 'client_argument', 'technician_argument')
    raw_id_fields = ('order', 'initiator')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('order', 'initiator', 'status', 'resolution', 'resolution_date')
        }),
        ('Arguments', {
            'fields': ('client_argument', 'technician_argument', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
