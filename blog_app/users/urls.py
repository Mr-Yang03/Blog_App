from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Web views (HTML templates)
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
]

# Note: API endpoints have been moved to the 'api' app
# See api/urls.py for all REST API endpoints
