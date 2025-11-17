from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'notificationpreferences', views.NotificationPreferenceViewSet, basename='notificationpreference')
router.register(r'notifications', views.NotificationViewSet, basename='notification')

urlpatterns = router.urls
