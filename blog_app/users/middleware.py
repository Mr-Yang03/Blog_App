"""
JWT Authentication Middleware for Web Views
Extracts JWT token from cookie and authenticates user
"""
from django.utils.functional import SimpleLazyObject
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser


def get_user_jwt(request):
    """
    Get user from JWT token in cookie or Authorization header
    """
    user = None
    jwt_auth = JWTAuthentication()
    
    # Try to get token from Authorization header first
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        try:
            validated_token = jwt_auth.get_validated_token(auth_header.split(' ')[1])
            user = jwt_auth.get_user(validated_token)
            return user
        except (InvalidToken, TokenError):
            pass
    
    # Try to get token from cookie
    token = request.COOKIES.get('access_token')
    if token:
        try:
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            return user
        except (InvalidToken, TokenError):
            pass
    
    return AnonymousUser()


class JWTAuthenticationMiddleware:
    """
    Middleware to authenticate users using JWT token from cookies or headers
    This allows web views to use JWT authentication like API views
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Don't override user if already authenticated via session
        if not hasattr(request, 'user') or request.user.is_anonymous:
            request.user = SimpleLazyObject(lambda: get_user_jwt(request))
        
        response = self.get_response(request)
        return response
