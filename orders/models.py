from django.db import models
from users.models import User
from services.models import Service
from datetime import date

class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    client_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_orders', null=False, blank=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=False, blank=False)
    technician_user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='technician_orders', null=True, blank=True)
    order_type = models.CharField(max_length=255, null=False, blank=False)
    problem_description = models.TextField(null=False, blank=False)
    requested_location = models.TextField(null=False, blank=False)
    scheduled_date = models.DateField(null=False, blank=False)
    scheduled_time_start = models.CharField(max_length=255, null=False, blank=False)
    scheduled_time_end = models.CharField(max_length=255, null=False, blank=False)
    ORDER_STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('ACCEPTED', 'Accepted'),
        ('IN_PROGRESS', 'In Progress'),
        ('AWAITING_RELEASE', 'Awaiting Release'),
        ('COMPLETED', 'Completed'),
        ('DISPUTED', 'Disputed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    order_status = models.CharField(max_length=50, choices=ORDER_STATUS_CHOICES, default='OPEN')
    initial_observations = models.TextField(blank=True, null=True)
    updated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    updated_schedule_date = models.DateField(null=True, blank=True)
    updated_schedule_time_start = models.CharField(max_length=255, null=True, blank=True)
    updated_schedule_time_end = models.CharField(max_length=255, null=True, blank=True)
    proposal_notes = models.TextField(blank=True, null=True)
    creation_timestamp = models.DateField(auto_now_add=True)
    job_start_timestamp = models.DateTimeField(null=True, blank=True)
    job_completion_timestamp = models.DateTimeField(null=True, blank=True) # When client releases funds or auto-release
    job_done_timestamp = models.DateTimeField(null=True, blank=True) # When technician marks job as done
    auto_release_date = models.DateTimeField(null=True, blank=True) # For automatic fund release
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    platform_commission_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    service_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    service_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount_paid_by_client = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount_to_technician = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'ORDER' # Explicitly set table name to match SQL

    def __str__(self):
        return f"Order {self.order_id} - {self.order_status}"

class Media(models.Model):
    media_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=False, blank=False)
    technician_user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='technician_media', null=True, blank=True)
    client_user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='client_media', null=True, blank=True)
    media_url = models.CharField(max_length=255, null=False, blank=False)
    media_type = models.CharField(max_length=255, null=False, blank=False)
    upload_date = models.DateField(null=False, blank=False)
    context = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'MEDIA'

    def __str__(self):
        return f"Media {self.media_id} - Type: {self.media_type}"

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
    OFFER_INITIATOR_CHOICES = [
        ('client', 'Client'),
        ('technician', 'Technician'),
    ]
    offer_initiator = models.CharField(max_length=20, choices=OFFER_INITIATOR_CHOICES, null=False, blank=False, default='technician')

    class Meta:
        db_table = 'PROJECT_OFFER'

    def __str__(self):
        return f"Offer {self.offer_id} for Order {self.order.order_id} by {self.technician_user.username}"

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
