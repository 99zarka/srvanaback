from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .google_login import GoogleLoginView

router = DefaultRouter()
router.register(r'usertypes', views.UserTypeViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'servicecategories', views.ServiceCategoryViewSet)
router.register(r'services', views.ServiceViewSet)
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
    path('register/', views.RegisterView.as_view(), name='register'),
    path('google-login/', GoogleLoginView.as_view(), name='google_login'),
]
