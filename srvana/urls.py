"""
URL configuration for srvana project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from users.views.custom_token_views import CustomTokenObtainPairView # Import your custom view
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings # Import settings

schema_view = get_schema_view(
   openapi.Info(
      title="Srvana API",
      default_version='v1',
      description="API documentation for the Srvana project",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@srvana.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   # Remove the 'url' parameter here to allow drf-yasg to auto-detect the scheme
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/', include('api.urls')),
    path('api/services/', include('services.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/technicians/', include('technicians.urls')),
    path('api/addresses/', include('addresses.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/issue_reports/', include('issue_reports.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'), # Use your custom view here
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api-auth/', include('rest_framework.urls')),
    path('api/files/', include('filesupload.urls')), # Include filesupload app URLs
]
