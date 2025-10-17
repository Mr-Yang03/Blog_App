"""
Login Required Middleware
Forces users to login before accessing any page except login/register
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings


class LoginRequiredMiddleware:
    """
    Middleware to require login for all views except explicitly allowed ones
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs that don't require authentication
        self.exempt_urls = [
            reverse('users:login'),
            reverse('users:register'),
        ]
        
        # URL patterns that don't require authentication (using startswith)
        self.exempt_url_patterns = [
            '/static/',
            '/media/',
            '/admin/',  # Keep admin accessible
            '/api/',  # All API endpoints (handled by DRF permissions)
        ]
    
    def __call__(self, request):
        # Get the current path
        path = request.path_info
        
        # Check if user is already authenticated
        if request.user.is_authenticated:
            return self.get_response(request)
        
        # Check if URL is in exempt list
        if path in self.exempt_urls:
            return self.get_response(request)
        
        # Check if URL matches exempt patterns
        for pattern in self.exempt_url_patterns:
            if path.startswith(pattern):
                return self.get_response(request)
        
        # User is not authenticated and trying to access protected page
        # Redirect to login with 'next' parameter
        login_url = settings.LOGIN_URL
        if not login_url.startswith('/'):
            login_url = reverse(login_url)
        
        # Add 'next' parameter to redirect back after login
        if path != '/':
            return redirect(f'{login_url}?next={path}')
        else:
            return redirect(login_url)
