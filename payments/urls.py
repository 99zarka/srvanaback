from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'paymentmethods', views.PaymentMethodViewSet, basename='paymentmethod')
router.register(r'payments', views.PaymentViewSet, basename='payment')

urlpatterns = router.urls
