from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'disputes', views.DisputeViewSet, basename='dispute')

urlpatterns = [
    path('<int:dispute_id>/resolve-dispute/', 
         views.DisputeViewSet.as_view({'post': 'resolve_dispute'}), 
         name='dispute-resolve'),
    path('', include(router.urls)),
]
