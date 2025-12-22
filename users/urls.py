from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import UserTypeViewSet, UserViewSet, RegisterView, client_dashboard_views
from users.views.current_user_views import CurrentUserView
from users.views.public_profile_views import PublicProfileView # Import PublicProfileView
from users.views.public_user_list_views import PublicUserViewSet # Import PublicUserViewSet
from .google_login import GoogleLoginView

app_name = 'users'

router = DefaultRouter()
router.register(r'usertypes', UserTypeViewSet)
router.register(r'users', UserViewSet)
router.register(r'public/all', PublicUserViewSet, basename='public_user') # Register PublicUserViewSet

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('google-login/', GoogleLoginView.as_view(), name='google_login'),
    path('me/', CurrentUserView.as_view(), name='current_user_profile'),
    path('public/<int:pk>/', PublicProfileView.as_view(), name='public_user_profile'), # New path for public user profiles
    # path('public/all/', PublicUserListView.as_view(), name='public_user_list'), # Removed, handled by router
    path('client_summary/', client_dashboard_views.ClientSummaryAPIView.as_view(), name='client_summary'),
    # Custom URLs for client-initiated offer flow
    path('users/<int:pk>/make-offer-to-technician/', 
         UserViewSet.as_view({'post': 'make_offer_to_technician'}), 
         name='user-make-offer-to-technician'),
    path('users/<int:pk>/offers/<int:offer_id>/respond-to-client-offer/', 
         UserViewSet.as_view({'post': 'respond_to_client_offer'}), 
         name='user-respond-to-client-offer'),
    # Profile photo endpoint
    path('users/<int:pk>/profile-photo/', 
         UserViewSet.as_view({'get': 'profile_photo'}), 
         name='user-profile-photo'),
]
