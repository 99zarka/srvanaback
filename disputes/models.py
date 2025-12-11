from django.db import models
from users.models import User
from orders.models import Order
from cloudinary.models import CloudinaryField

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

    class Meta:
        db_table = 'DISPUTE'
        indexes = [
            models.Index(fields=['order', '-created_at']),  # For getting disputes by order, most recent first
            models.Index(fields=['status', '-created_at']),  # For status-based queries
            models.Index(fields=['initiator', '-created_at']),  # For initiator-based queries
            models.Index(fields=['order', 'status']),  # For order + status queries
        ]

    def __str__(self):
        return f"Dispute {self.dispute_id} for Order {self.order.order_id} - Status: {self.status}"

class DisputeResponse(models.Model):
    """
    Model to store responses/replies in a dispute conversation between client and technician
    """
    RESPONSE_TYPE_CHOICES = [
        ('CLIENT', 'Client'),
        ('TECHNICIAN', 'Technician'),
        ('ADMIN', 'Admin'),
    ]

    dispute = models.ForeignKey(Dispute, on_delete=models.CASCADE, related_name='responses')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dispute_responses')
    response_type = models.CharField(max_length=20, choices=RESPONSE_TYPE_CHOICES)
    message = models.TextField()
    file_url = CloudinaryField('dispute_response_files', null=True, blank=True)  # For Cloudinary file uploads
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'DISPUTE_RESPONSE'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['dispute', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
        ]

    def __str__(self):
        return f"Response {self.id} in Dispute {self.dispute.dispute_id} - {self.response_type}"
