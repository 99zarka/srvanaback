from django.db import models
from users.models import User
from orders.models import Order

class Dispute(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_REVIEW', 'In Review'),
        ('RESOLVED', 'Resolved'),
    ]

    RESOLUTION_CHOICES = [
        ('PAY_TECHNICIAN', 'Pay Technician'),
        ('REFUND_CLIENT', 'Refund Client'),
        ('SPLIT_PAYMENT', 'Split Payment'),
    ]

    dispute_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='disputes')
    initiator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_disputes')
    client_argument = models.TextField(null=True, blank=True)
    technician_argument = models.TextField(null=True, blank=True)
    admin_notes = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    resolution = models.CharField(max_length=50, choices=RESOLUTION_CHOICES, null=True, blank=True)
    resolution_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True) # Renamed from initiated_date
    # Removed resolved_amount_to_client and resolved_amount_to_technician as these amounts will be handled via Transactions
    # Removed technician_user and admin_reviewer, as these are implicitly handled by the order and admin_notes.

    class Meta:
        db_table = 'DISPUTE'

    def __str__(self):
        return f"Dispute {self.dispute_id} for Order {self.order.order_id} - Status: {self.status}"
