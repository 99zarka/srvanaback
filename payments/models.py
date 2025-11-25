from django.db import models
from users.models import User
from orders.models import Order # Import Order model

class PaymentMethod(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    card_type = models.CharField(max_length=50)  # e.g., Visa, MasterCard, American Express
    last_four_digits = models.CharField(max_length=4)
    expiration_date = models.CharField(max_length=7)  # MM/YYYY
    card_holder_name = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Payment Methods"
        unique_together = ('user', 'card_type', 'last_four_digits')

    def __str__(self):
        return f"{self.card_type} ending in {self.last_four_digits}"

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
