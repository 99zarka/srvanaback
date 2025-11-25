from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import UserTypeViewSet, UserViewSet, RegisterView, client_dashboard_views
from users.views.current_user_views import CurrentUserView
from users.views.public_profile_views import PublicProfileView # Import PublicProfileView
from users.views.public_user_list_views import PublicUserListView # Import PublicUserListView
from .google_login import GoogleLoginView

router = DefaultRouter()
router.register(r'usertypes', UserTypeViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('google-login/', GoogleLoginView.as_view(), name='google_login'),
    path('me/', CurrentUserView.as_view(), name='current_user_profile'),
    path('public/<int:pk>/', PublicProfileView.as_view(), name='public_user_profile'), # New path for public user profiles
    path('public/all/', PublicUserListView.as_view(), name='public_user_list'), # New path for public user list with pagination
    path('client_summary/', client_dashboard_views.ClientSummaryAPIView.as_view(), name='client_summary'),
]
