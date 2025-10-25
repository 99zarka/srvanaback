from rest_framework import viewsets
from .models.users import User, UserType
from .models.services import ServiceCategory, Service
from .models.technicians import TechnicianAvailability, TechnicianSkill, VerificationDocument
from .models.orders.core import Order
from .serializers import (
    UserTypeSerializer, UserSerializer,
    ServiceCategorySerializer, ServiceSerializer,
    TechnicianAvailabilitySerializer, TechnicianSkillSerializer,
    VerificationDocumentSerializer, OrderSerializer
)

class UserTypeViewSet(viewsets.ModelViewSet):
    queryset = UserType.objects.all()
    serializer_class = UserTypeSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ServiceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

class TechnicianAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = TechnicianAvailability.objects.all()
    serializer_class = TechnicianAvailabilitySerializer

class TechnicianSkillViewSet(viewsets.ModelViewSet):
    queryset = TechnicianSkill.objects.all()
    serializer_class = TechnicianSkillSerializer

class VerificationDocumentViewSet(viewsets.ModelViewSet):
    queryset = VerificationDocument.objects.all()
    serializer_class = VerificationDocumentSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
