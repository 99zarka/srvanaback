from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'paymentmethods', views.PaymentMethodViewSet, basename='paymentmethod')

urlpatterns = router.urls
