"""
Custom middleware to bypass CSRF checking for development/testing purposes.
This should only be used in development environments.
"""

class DisableCSRFMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Disable CSRF protection for all requests
        setattr(request, '_dont_enforce_csrf_checks', True)
        response = self.get_response(request)
        return response
