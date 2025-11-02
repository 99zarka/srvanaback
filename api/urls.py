from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserTypeViewSet, UserViewSet, RegisterView,
    ServiceCategoryViewSet, ServiceViewSet,
    TechnicianAvailabilityViewSet, TechnicianSkillViewSet,
    VerificationDocumentViewSet, OrderViewSet, ProjectOfferViewset,
    AddressViewSet, PaymentMethodViewSet, NotificationPreferenceViewSet,
    NotificationViewSet, ReviewViewSet, IssueReportViewSet,
    TransactionViewSet, ConversationViewSet, MessageViewSet
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
router.register(r'projectoffers', ProjectOfferViewset)
router.register(r'addresses', AddressViewSet)
router.register(r'paymentmethods', PaymentMethodViewSet)
router.register(r'notificationpreferences', NotificationPreferenceViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'issuereports', IssueReportViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'conversations', ConversationViewSet)
router.register(r'messages', MessageViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
]
