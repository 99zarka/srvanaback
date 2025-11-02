from django.db import models
from ..users import User
from .core import Order # Import Order from core.py
from datetime import date

class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=False, blank=False)
    client_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_payments', null=False, blank=False)
    payment_method = models.CharField(max_length=255, null=False, blank=False)
    transaction_id = models.CharField(max_length=255, null=False, blank=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    payment_date = models.DateField(null=False, blank=False)
    payment_status = models.CharField(max_length=255, null=False, blank=False)
    is_deposit = models.BooleanField(null=False, blank=False)

    class Meta:
        db_table = 'PAYMENT'

    def __str__(self):
        return f"Payment {self.payment_id} for Order {self.order.order_id}"
