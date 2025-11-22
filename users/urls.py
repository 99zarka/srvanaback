from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import UserTypeViewSet, UserViewSet, RegisterView
from users.views.current_user_views import CurrentUserView
from .google_login import GoogleLoginView

router = DefaultRouter()
router.register(r'usertypes', UserTypeViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('google-login/', GoogleLoginView.as_view(), name='google_login'),
    path('me/', CurrentUserView.as_view(), name='current_user_profile'),
]
