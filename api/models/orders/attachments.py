from django.db import models
from users.models import User
from .core import Order # Import Order from core.py
from datetime import date

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
