from django.db import models
from users.models import User
from .orders.core import Order

class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews', null=True, blank=True)
    technician = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews', null=True, blank=True) # Assuming technician is a User
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('order', 'reviewer')

    def __str__(self):
        return f"Review for Order {self.order.id} by {self.reviewer.username}"
