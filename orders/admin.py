from django.contrib import admin
from .models import Order, Payment, ProjectOffer, Complaint, Media

admin.site.register(Order)
admin.site.register(Payment)
admin.site.register(ProjectOffer)
admin.site.register(Complaint)
admin.site.register(Media)
