from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'transactions', views.TransactionViewSet, basename='transaction')

urlpatterns = router.urls
