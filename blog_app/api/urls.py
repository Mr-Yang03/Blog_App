"""
API URLs - Centralized URL routing for all API endpoints
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'api'

urlpatterns = [
    # ========================================
    # AUTHENTICATION ENDPOINTS
    # ========================================
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', views.UserProfileView.as_view(), name='profile'),
    path('auth/profile/update/', views.UpdateProfileView.as_view(), name='profile_update'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('auth/delete-account/', views.DeleteAccountView.as_view(), name='delete_account'),

    # ========================================
    # USER ENDPOINTS
    # ========================================
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),

    # ========================================
    # CATEGORY ENDPOINTS
    # ========================================
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('categories/<slug:category_slug>/posts/', views.post_by_category, name='category_posts'),

    # ========================================
    # TAG ENDPOINTS
    # ========================================
    path('tags/', views.TagListView.as_view(), name='tag_list'),
    path('tags/create/', views.TagCreateView.as_view(), name='tag_create'),
    path('tags/<int:pk>/', views.TagDetailView.as_view(), name='tag_detail'),
    path('tags/<slug:tag_slug>/posts/', views.post_by_tag, name='tag_posts'),

    # ========================================
    # POST ENDPOINTS
    # ========================================
    path('posts/', views.PostListView.as_view(), name='post_list'),
    path('posts/create/', views.PostCreateView.as_view(), name='post_create'),
    path('posts/my-posts/', views.MyPostsView.as_view(), name='my_posts'),
    path('posts/trending/', views.TrendingPostsView.as_view(), name='trending_posts'),
    path('posts/featured/', views.FeaturedPostsView.as_view(), name='featured_posts'),
    path('posts/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('posts/<slug:slug>/update/', views.PostUpdateView.as_view(), name='post_update'),
    path('posts/<slug:slug>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('posts/<slug:slug>/stats/', views.PostStatsView.as_view(), name='post_stats'),
    path('posts/<slug:slug>/like/', views.LikePostView.as_view(), name='post_like'),
    path('posts/<slug:slug>/likes/', views.PostLikesView.as_view(), name='post_likes'),

    # ========================================
    # COMMENT ENDPOINTS
    # ========================================
    path('posts/<int:post_id>/comments/', views.CommentListView.as_view(), name='comment_list'),
    path('posts/<int:post_id>/comments/create/', views.CommentCreateView.as_view(), name='comment_create'),
    path('comments/<int:pk>/update/', views.CommentUpdateView.as_view(), name='comment_update'),
    path('comments/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),

    # ========================================
    # SEARCH & FILTER ENDPOINTS
    # ========================================
    path('search/', views.search_posts, name='search_posts'),
]
