from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'technicianavailabilities', views.TechnicianAvailabilityViewSet, basename='technicianavailability')
router.register(r'technicianskills', views.TechnicianSkillViewSet, basename='technicianskill')
router.register(r'verificationdocuments', views.VerificationDocumentViewSet, basename='verificationdocument')

urlpatterns = router.urls
