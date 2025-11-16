from django.db import models
from users.models import User
from .services import Service

class TechnicianAvailability(models.Model):
    availability_id = models.AutoField(primary_key=True)
    technician_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availabilities', null=False, blank=False)
    day_of_week = models.CharField(max_length=255, null=False, blank=False)
    start_time = models.CharField(max_length=255, null=False, blank=False) # Storing as CharField for flexibility with time formats
    end_time = models.CharField(max_length=255, null=False, blank=False) # Storing as CharField for flexibility with time formats
    is_available = models.BooleanField(null=False, blank=False)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    experience_years = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'TECHNICIAN_AVAILABILITY'

    def __str__(self):
        return f"{self.technician_user.username}'s availability on {self.day_of_week}"

class TechnicianSkill(models.Model):
    technician_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills', null=False, blank=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=False, blank=False)
    experience_level = models.CharField(max_length=255, null=False, blank=False)

    class Meta:
        db_table = 'TECHNICIAN_SKILL'
        unique_together = (('technician_user', 'service'),) # Composite primary key

    def __str__(self):
        return f"{self.technician_user.username} - {self.service.service_name} ({self.experience_level})"

class VerificationDocument(models.Model):
    doc_id = models.AutoField(primary_key=True)
    technician_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_documents', null=False, blank=False)
    document_type = models.CharField(max_length=255, null=False, blank=False)
    document_url = models.CharField(max_length=255, null=False, blank=False)
    upload_date = models.DateField(null=False, blank=False)
    verification_status = models.CharField(max_length=255, null=False, blank=False)
    rejection_reason = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'VERIFICATION_DOCUMENT'

    def __str__(self):
        return f"Document {self.doc_id} - Type: {self.document_type} - Status: {self.verification_status}"
