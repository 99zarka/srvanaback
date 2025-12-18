from django.db import models
from users.models import User
from orders.models import Order # Import Order model

class PaymentMethod(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    paymob_token = models.CharField(max_length=255, unique=True, null=True, blank=True) # Secure token from Paymob
    masked_pan = models.CharField(max_length=20, default='****') # Last 4 digits (or masked)
    card_type = models.CharField(max_length=50, null=True, blank=True)  # e.g., Visa, MasterCard (card_subtype)
    expiration_date = models.CharField(max_length=7, null=True, blank=True)  # MM/YYYY
    card_holder_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True) # Optional email associated with card
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Payment Methods"
        unique_together = ('user', 'masked_pan', 'card_type') # Prevent duplicate cards per user

    def __str__(self):
        return f"{self.card_type} ending in {self.masked_pan}"

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status_choices = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    status = models.CharField(max_length=50, choices=status_choices, default='PENDING')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Payment of {self.amount} for Order {self.order_id} - {self.status}"
