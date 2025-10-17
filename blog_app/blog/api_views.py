from rest_framework import generics, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from .models import Post, Category, Tag, Comment, Like
from .serializers import (
    PostListSerializer,
    PostDetailSerializer,
    PostCreateUpdateSerializer,
    CategorySerializer,
    TagSerializer,
    CommentSerializer,
    LikeSerializer,
    PostStatsSerializer
)
from users.permissions import IsOwnerOrReadOnly


class CategoryListView(generics.ListAPIView):
    """
    List all categories
    GET /api/categories/
    """
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class CategoryDetailView(generics.RetrieveAPIView):
    """
    Get category details
    GET /api/categories/<id>/
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class CategoryCreateView(generics.CreateAPIView):
    """
    Create new category (Admin only)
    POST /api/categories/create/
    Body: {"name": "Technology", "description": "Tech posts"}
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]


class TagListView(generics.ListAPIView):
    """
    List all tags
    GET /api/tags/
    """
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class TagDetailView(generics.RetrieveAPIView):
    """
    Get tag details
    GET /api/tags/<id>/
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class TagCreateView(generics.CreateAPIView):
    """
    Create new tag (Admin only)
    POST /api/tags/create/
    Body: {"name": "Python"}
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAdminUser]


class PostListView(generics.ListAPIView):
    """
    List all published posts with search and filter
    GET /api/posts/
    Query params:
    - search: Search in title, content, author username
    - category: Filter by category ID
    - tag: Filter by tag ID
    - author: Filter by author username
    - ordering: Order by field (e.g., -created_at, views_count)
    """
    serializer_class = PostListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content', 'author__username']
    ordering_fields = ['created_at', 'published_at', 'views_count', 'title']
    ordering = ['-published_at']

    def get_queryset(self):
        """Filter posts based on query parameters"""
        queryset = Post.objects.filter(status='published').select_related(
            'author', 'category'
        ).prefetch_related('tags', 'likes', 'comments')

        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Filter by tag
        tag_id = self.request.query_params.get('tag')
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)

        # Filter by author
        author_username = self.request.query_params.get('author')
        if author_username:
            queryset = queryset.filter(author__username=author_username)

        # Filter featured posts
        is_featured = self.request.query_params.get('featured')
        if is_featured and is_featured.lower() == 'true':
            queryset = queryset.filter(is_featured=True)

        return queryset.distinct()


class PostDetailView(generics.RetrieveAPIView):
    """
    Get post details by slug
    GET /api/posts/<slug>/
    Automatically increments view count
    """
    queryset = Post.objects.filter(status='published').select_related(
        'author', 'category'
    ).prefetch_related('tags', 'comments', 'likes')
    serializer_class = PostDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        """Increment view count when post is retrieved"""
        instance = self.get_object()

        # Increment views
        instance.views_count += 1
        instance.save(update_fields=['views_count'])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class PostCreateView(generics.CreateAPIView):
    """
    Create new post (Authenticated users only)
    POST /api/posts/create/
    Body: {
        "title": "My Post",
        "content": "Post content...",
        "excerpt": "Short description",
        "category_id": 1,
        "tag_ids": [1, 2],
        "status": "draft",
        "is_featured": false
    }
    """
    queryset = Post.objects.all()
    serializer_class = PostCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Set author to current user"""
        serializer.save(author=self.request.user)


class PostUpdateView(generics.UpdateAPIView):
    """
    Update post (Owner or Admin only)
    PUT/PATCH /api/posts/<slug>/update/
    """
    queryset = Post.objects.all()
    serializer_class = PostCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        """Only allow users to update their own posts"""
        if self.request.user.is_staff:
            return Post.objects.all()
        return Post.objects.filter(author=self.request.user)


class PostDeleteView(generics.DestroyAPIView):
    """
    Delete post (Owner or Admin only)
    DELETE /api/posts/<slug>/delete/
    """
    queryset = Post.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        """Only allow users to delete their own posts"""
        if self.request.user.is_staff:
            return Post.objects.all()
        return Post.objects.filter(author=self.request.user)


class MyPostsView(generics.ListAPIView):
    """
    List current user's posts (all statuses)
    GET /api/posts/my-posts/
    """
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only current user's posts"""
        return Post.objects.filter(author=self.request.user).select_related(
            'category', 'author'
        ).prefetch_related('tags', 'comments', 'likes').order_by('-created_at')


class CommentListView(generics.ListAPIView):
    """
    List comments for a specific post
    GET /api/posts/<post_id>/comments/
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Get comments for specific post"""
        post_id = self.kwargs.get('post_id')
        return Comment.objects.filter(
            post_id=post_id,
            parent=None,  # Only top-level comments
            is_approved=True
        ).select_related('author').prefetch_related('replies').order_by('-created_at')


class CommentCreateView(generics.CreateAPIView):
    """
    Create comment on a post
    POST /api/posts/<post_id>/comments/create/
    Body: {
        "content": "Great post!",
        "parent": null  // or parent comment ID for reply
    }
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Set author and post"""
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id, status='published')
        serializer.save(author=self.request.user, post=post)


class CommentUpdateView(generics.UpdateAPIView):
    """
    Update own comment
    PUT/PATCH /api/comments/<id>/update/
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """Only allow users to update their own comments"""
        if self.request.user.is_staff:
            return Comment.objects.all()
        return Comment.objects.filter(author=self.request.user)


class CommentDeleteView(generics.DestroyAPIView):
    """
    Delete own comment
    DELETE /api/comments/<id>/delete/
    """
    queryset = Comment.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """Only allow users to delete their own comments"""
        if self.request.user.is_staff:
            return Comment.objects.all()
        return Comment.objects.filter(author=self.request.user)


class LikePostView(APIView):
    """
    Toggle like on a post
    POST /api/posts/<slug>/like/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        """Toggle like status"""
        post = get_object_or_404(Post, slug=slug, status='published')
        user = request.user

        # Check if already liked
        like = Like.objects.filter(post=post, user=user).first()

        if like:
            # Unlike
            like.delete()
            return Response({
                'message': 'Post unliked',
                'liked': False,
                'likes_count': post.likes.count()
            }, status=status.HTTP_200_OK)
        else:
            # Like
            Like.objects.create(post=post, user=user)
            return Response({
                'message': 'Post liked',
                'liked': True,
                'likes_count': post.likes.count()
            }, status=status.HTTP_201_CREATED)


class PostLikesView(generics.ListAPIView):
    """
    List all users who liked a post
    GET /api/posts/<slug>/likes/
    """
    serializer_class = LikeSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Get likes for specific post"""
        slug = self.kwargs.get('slug')
        post = get_object_or_404(Post, slug=slug)
        return Like.objects.filter(post=post).select_related('user').order_by('-created_at')


class PostStatsView(generics.RetrieveAPIView):
    """
    Get post statistics
    GET /api/posts/<slug>/stats/
    """
    queryset = Post.objects.all()
    serializer_class = PostStatsSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'


class TrendingPostsView(generics.ListAPIView):
    """
    Get trending posts (most viewed in last 7 days)
    GET /api/posts/trending/
    """
    serializer_class = PostListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Get most viewed posts"""
        from django.utils import timezone
        from datetime import timedelta

        week_ago = timezone.now() - timedelta(days=7)
        return Post.objects.filter(
            status='published',
            published_at__gte=week_ago
        ).order_by('-views_count')[:10]


class FeaturedPostsView(generics.ListAPIView):
    """
    Get featured posts
    GET /api/posts/featured/
    """
    queryset = Post.objects.filter(
        status='published',
        is_featured=True
    ).order_by('-published_at')[:5]
    serializer_class = PostListSerializer
    permission_classes = [permissions.AllowAny]


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_posts(request):
    """
    Advanced search posts
    GET /api/posts/search/?q=keyword&category=1&tag=2&author=username
    """
    query = request.GET.get('q', '')
    category_id = request.GET.get('category')
    tag_id = request.GET.get('tag')
    author = request.GET.get('author')

    posts = Post.objects.filter(status='published')

    # Text search
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(author__username__icontains=query)
        )

    # Filter by category
    if category_id:
        posts = posts.filter(category_id=category_id)

    # Filter by tag
    if tag_id:
        posts = posts.filter(tags__id=tag_id)

    # Filter by author
    if author:
        posts = posts.filter(author__username=author)

    posts = posts.select_related('author', 'category').prefetch_related(
        'tags', 'comments', 'likes'
    ).distinct().order_by('-published_at')

    serializer = PostListSerializer(posts, many=True, context={'request': request})
    return Response({
        'count': posts.count(),
        'results': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def post_by_category(request, category_slug):
    """
    Get posts by category slug
    GET /api/categories/<slug>/posts/
    """
    category = get_object_or_404(Category, slug=category_slug)
    posts = Post.objects.filter(
        category=category,
        status='published'
    ).select_related('author', 'category').prefetch_related(
        'tags', 'comments', 'likes'
    ).order_by('-published_at')

    serializer = PostListSerializer(posts, many=True, context={'request': request})
    return Response({
        'category': CategorySerializer(category).data,
        'posts': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def post_by_tag(request, tag_slug):
    """
    Get posts by tag slug
    GET /api/tags/<slug>/posts/
    """
    tag = get_object_or_404(Tag, slug=tag_slug)
    posts = Post.objects.filter(
        tags=tag,
        status='published'
    ).select_related('author', 'category').prefetch_related(
        'tags', 'comments', 'likes'
    ).order_by('-published_at')

    serializer = PostListSerializer(posts, many=True, context={'request': request})
    return Response({
        'tag': TagSerializer(tag).data,
        'posts': serializer.data
    })
