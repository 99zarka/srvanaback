from django.db import models
from .users import User

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
