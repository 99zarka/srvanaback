from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'technicianavailabilities', views.TechnicianAvailabilityViewSet)
router.register(r'technicianskills', views.TechnicianSkillViewSet)
router.register(r'verificationdocuments', views.VerificationDocumentViewSet)
router.register(r'orders', views.OrderViewSet)
router.register(r'projectoffers', views.ProjectOfferViewset)
router.register(r'addresses', views.AddressViewSet)
router.register(r'paymentmethods', views.PaymentMethodViewSet)
router.register(r'notificationpreferences', views.NotificationPreferenceViewSet)
router.register(r'notifications', views.NotificationViewSet)
router.register(r'reviews', views.ReviewViewSet)
router.register(r'issuereports', views.IssueReportViewSet)
router.register(r'transactions', views.TransactionViewSet)
router.register(r'conversations', views.ConversationViewSet)
router.register(r'messages', views.MessageViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
