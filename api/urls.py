from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserTypeViewSet, UserViewSet,
    ServiceCategoryViewSet, ServiceViewSet,
    TechnicianAvailabilityViewSet, TechnicianSkillViewSet,
    VerificationDocumentViewSet, OrderViewSet
)

router = DefaultRouter()
router.register(r'usertypes', UserTypeViewSet)
router.register(r'users', UserViewSet)
router.register(r'servicecategories', ServiceCategoryViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'technicianavailabilities', TechnicianAvailabilityViewSet)
router.register(r'technicianskills', TechnicianSkillViewSet)
router.register(r'verificationdocuments', VerificationDocumentViewSet)
router.register(r'orders', OrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
