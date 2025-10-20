from django.db import models
from ..users import User
from .core import Order # Import Order from core.py
from datetime import date

class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=False, blank=False)
    client_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_reviews', null=False, blank=False)
    technician_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='technician_reviews', null=False, blank=False)
    rating = models.IntegerField(null=False, blank=False)
    comment = models.TextField(null=True, blank=True)
    review_date = models.DateField(null=False, blank=False)

    class Meta:
        db_table = 'REVIEW'

    def __str__(self):
        return f"Review {self.review_id} - Rating: {self.rating}"

class Complaint(models.Model):
    complaint_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=False, blank=False)
    client_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_complaints', null=False, blank=False)
    technician_user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='technician_complaints', null=True, blank=True)
    complaint_details = models.TextField(null=False, blank=False)
    submission_date = models.DateField(null=False, blank=False)
    status = models.CharField(max_length=255, null=False, blank=False)
    admin_user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='admin_complaints', null=True, blank=True)
    resolution_details = models.TextField(null=True, blank=True)
    resolution_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'COMPLAINT'

    def __str__(self):
        return f"Complaint {self.complaint_id} - Status: {self.status}"
