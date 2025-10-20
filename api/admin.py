from django.contrib import admin
from .models import (
    UserType, User, ServiceCategory, Service, Order, Payment, Review,
    TechnicianAvailability, TechnicianSkill, ProjectOffer, Complaint, Media,
    VerificationDocument
)

admin.site.register(UserType)
admin.site.register(User)
admin.site.register(ServiceCategory)
admin.site.register(Service)
admin.site.register(Order)
admin.site.register(Payment)
admin.site.register(Review)
admin.site.register(TechnicianAvailability)
admin.site.register(TechnicianSkill)
admin.site.register(ProjectOffer)
admin.site.register(Complaint)
admin.site.register(Media)
admin.site.register(VerificationDocument)
