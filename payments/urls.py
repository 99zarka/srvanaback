from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'paymentmethods', views.PaymentMethodViewSet, basename='paymentmethod')
router.register(r'', views.PaymentViewSet, basename='payment') # Removed redundant prefix

urlpatterns = [
    path('transfer-pending-to-available/', views.PaymentViewSet.as_view({'post': 'transfer_pending_to_available'}), name='transfer-pending-to-available'),
]
urlpatterns += router.urls
