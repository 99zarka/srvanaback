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

class ProjectOffer(models.Model):
    offer_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=False, blank=False)
    technician_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offers', null=False, blank=False)
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    estimated_completion_time = models.CharField(max_length=255, null=True, blank=True)
    offer_notes = models.TextField(null=True, blank=True)
    offer_date = models.DateField(null=False, blank=False)
    offer_status = models.CharField(max_length=255, null=False, blank=False)

    class Meta:
        db_table = 'PROJECT_OFFER'

    def __str__(self):
        return f"Offer {self.offer_id} for Order {self.order.order_id}"
