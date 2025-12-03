from rest_framework import authentication, permissions
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import AnonymousUser
from rest_framework import HTTP_HEADER_ENCODING


class CustomAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication that returns 403 instead of 401 for unauthenticated users.
    """
    def authenticate(self, request):
        """
        Returns a tuple of (user, auth) if authentication is successful,
        or raises an AuthenticationFailed exception if not.
        """
        # First, try Django's default authentication
        user = getattr(request._request, 'user', None)
        
        # If no user attribute, try to extract credentials manually
        if user is None:
            user = self._authenticate_header(request)
        
        if user is None:
            # Instead of raising an exception, return None to let permission system handle it
            return None
        
        if isinstance(user, AnonymousUser):
            return None
            
        return (user, None)

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 UNAUTHORIZED` response.
        """
        # Return a generic auth header instead of triggering 401
        return 'Authentication required'


class IsAuthenticatedOrForbidden(permissions.BasePermission):
    """
    Custom permission that returns 403 instead of 401 for unauthenticated users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True
