from django.db import models
from users.models import User
from orders.models import Order
from disputes.models import Dispute # Uncommented

class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('ESCROW_HOLD', 'Escrow Hold'),
        ('ESCROW_RELEASE', 'Escrow Release'),
        ('CANCEL_REFUND', 'Cancel Refund'),
        ('DISPUTE_PAYOUT', 'Dispute Payout'),
        ('DISPUTE_REFUND', 'Dispute Refund'),
        ('FEE', 'Fee'),
        ('PENDING_TO_AVAILABLE_TRANSFER', 'Pending To Available Transfer'),
    ]

    source_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_transactions', null=True, blank=True)
    destination_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_transactions', null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    dispute = models.ForeignKey(Dispute, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EGP')
    # Removed status choices as per implementation plan, transactions are typically either created or not.
    payment_method = models.CharField(max_length=255, null=True, blank=True) # e.g., 'Credit Card', 'Wallet'
    transaction_id = models.CharField(max_length=255, null=True, blank=True) # From payment gateway, not necessarily unique across all transactions (e.g., refunds)
    timestamp = models.DateTimeField(auto_now_add=True) # Renamed from created_at for clarity and consistency
    # Removed updated_at as it's not explicitly needed for transactions once created

    def __str__(self):
        return f"Transaction {self.id} ({self.transaction_type})"
