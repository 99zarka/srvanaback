from django.contrib import admin
from .models import TechnicianAvailability, TechnicianSkill, VerificationDocument

admin.site.register(TechnicianAvailability)
admin.site.register(TechnicianSkill)
admin.site.register(VerificationDocument)
