"""
Authentication Middleware
Lightweight middleware for logging and role validation.
"""
import logging
from django.http import JsonResponse

logger = logging.getLogger('edoc_hms')

# URL prefixes that require no authentication
PUBLIC_PATHS = [
    '/api/auth/login/',
    '/api/auth/register/',
    '/api/auth/token/refresh/',
    '/api/doctors/',
    '/api/schedules/',
    '/admin/',
]

class RoleBasedAccessMiddleware:
    """
    Middleware that logs requests and can enforce coarse-grained
    role validation before DRF permission classes run.
    This is intentionally lightweight — DRF handles fine-grained RBAC.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log incoming API requests
        if request.path.startswith('/api/'):
            user_info = request.user if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
            logger.debug(f"API Request: {request.method} {request.path} | User: {user_info}")

        response = self.get_response(request)
        return response
