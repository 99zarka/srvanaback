from django.db import models
from ..users import User
from ..services import Service
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
    order_status = models.CharField(max_length=255, null=False, blank=False)
    creation_timestamp = models.DateField(null=False, blank=False)
    job_start_timestamp = models.DateField(null=True, blank=True)
    job_completion_timestamp = models.DateField(null=True, blank=True)
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
