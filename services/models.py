from django.db import models
from users.models import User # Import User for ForeignKey in other models

class ServiceCategory(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    icon_url = models.ImageField(upload_to='service_category_icons/', null=True, blank=True)

    class Meta:
        db_table = 'SERVICE_CATEGORY'

    def __str__(self):
        return self.category_name

class Service(models.Model):
    service_id = models.AutoField(primary_key=True)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, null=False, blank=False)
    service_name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    service_type = models.CharField(max_length=255, null=False, blank=False)
    base_inspection_fee = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    estimated_price_range_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_price_range_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    emergency_surcharge_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # e.g., 99.99%

    class Meta:
        db_table = 'SERVICE'

    def __str__(self):
        return self.service_name
