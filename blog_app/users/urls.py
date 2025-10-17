from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views, api_views

app_name = 'users'

urlpatterns = [
    # Web views (HTML templates)
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),

    # API endpoints (JWT)
    path('api/auth/register/', api_views.RegisterView.as_view(), name='api_register'),
    path('api/auth/login/', api_views.CustomTokenObtainPairView.as_view(), name='api_login'),
    path('api/auth/logout/', api_views.LogoutView.as_view(), name='api_logout'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/profile/', api_views.UserProfileView.as_view(), name='api_profile'),
    path('api/auth/profile/update/', api_views.UpdateProfileView.as_view(), name='api_profile_update'),
    path('api/auth/change-password/', api_views.ChangePasswordView.as_view(), name='api_change_password'),
    path('api/auth/delete-account/', api_views.DeleteAccountView.as_view(), name='api_delete_account'),
    path('api/users/', api_views.UserListView.as_view(), name='api_user_list'),
    path('api/users/<int:pk>/', api_views.UserDetailView.as_view(), name='api_user_detail'),
]
