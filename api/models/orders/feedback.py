from django.db import models
from ..users import User
from .core import Order # Import Order from core.py
from datetime import date

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

class ProjectOffer(models.Model):
    offer_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='project_offers', null=False, blank=False)
    technician_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offered_projects', null=False, blank=False)
    offered_price = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    offer_description = models.TextField(null=True, blank=True)
    offer_date = models.DateField(null=False, blank=False)
    status = models.CharField(max_length=255, null=False, blank=False) # e.g., 'pending', 'accepted', 'rejected'

    class Meta:
        db_table = 'PROJECT_OFFER'

    def __str__(self):
        return f"Offer {self.offer_id} for Order {self.order.order_id} by {self.technician_user.username}"
