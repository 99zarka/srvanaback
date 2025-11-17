from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'addresses', views.AddressViewSet)
router.register(r'paymentmethods', views.PaymentMethodViewSet)
router.register(r'notificationpreferences', views.NotificationPreferenceViewSet)
router.register(r'notifications', views.NotificationViewSet)
router.register(r'reviews', views.ReviewViewSet)
router.register(r'issuereports', views.IssueReportViewSet)
router.register(r'transactions', views.TransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
