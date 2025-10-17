from rest_framework import serializers
from .models import Category, Tag, Post, Comment, Like
from users.serializers import UserSerializer


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'created_at', 'post_count']
        read_only_fields = ['id', 'slug', 'created_at']

    def get_post_count(self, obj):
        """Get total number of published posts in this category"""
        return obj.posts.filter(status='published').count()


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model"""
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'created_at', 'post_count']
        read_only_fields = ['id', 'slug', 'created_at']

    def get_post_count(self, obj):
        """Get total number of published posts with this tag"""
        return obj.posts.filter(status='published').count()


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model"""
    author = UserSerializer(read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    replies = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'author_username', 'parent', 'content',
                  'is_approved', 'created_at', 'updated_at', 'replies', 'replies_count']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'is_approved']

    def get_replies(self, obj):
        """Get all replies to this comment (recursive)"""
        if obj.replies.exists():
            return CommentSerializer(
                obj.replies.filter(is_approved=True),
                many=True,
                context=self.context
            ).data
        return []

    def get_replies_count(self, obj):
        """Get total number of replies"""
        return obj.replies.filter(is_approved=True).count()

    def create(self, validated_data):
        """Create comment with current user as author"""
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class PostListSerializer(serializers.ModelSerializer):
    """Serializer for Post list view (lightweight)"""
    author = UserSerializer(read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    read_time = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'author', 'author_username', 'excerpt',
                  'featured_image', 'category', 'category_name', 'tags', 'status',
                  'views_count', 'is_featured', 'published_at', 'created_at',
                  'likes_count', 'comments_count', 'read_time']
        read_only_fields = ['id', 'slug', 'author', 'views_count', 'created_at']

    def get_likes_count(self, obj):
        """Get total number of likes"""
        return obj.likes.count()

    def get_comments_count(self, obj):
        """Get total number of approved comments"""
        return obj.comments.filter(is_approved=True).count()

    def get_read_time(self, obj):
        """Calculate estimated reading time in minutes"""
        words = len(obj.content.split())
        minutes = max(1, words // 200)  # Average reading speed: 200 words/minute
        return minutes


class PostDetailSerializer(serializers.ModelSerializer):
    """Serializer for Post detail view (full content)"""
    author = UserSerializer(read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source='tags',
        many=True,
        write_only=True,
        required=False
    )
    comments = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    read_time = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'author', 'author_username', 'content',
                  'excerpt', 'featured_image', 'category', 'category_id', 'tags',
                  'tag_ids', 'status', 'views_count', 'is_featured', 'published_at',
                  'created_at', 'updated_at', 'comments', 'likes_count',
                  'comments_count', 'read_time', 'user_has_liked']
        read_only_fields = ['id', 'slug', 'author', 'views_count', 'created_at', 'updated_at']

    def get_comments(self, obj):
        """Get top-level comments (no parent)"""
        comments = obj.comments.filter(parent=None, is_approved=True).order_by('-created_at')
        return CommentSerializer(comments, many=True, context=self.context).data

    def get_likes_count(self, obj):
        """Get total number of likes"""
        return obj.likes.count()

    def get_comments_count(self, obj):
        """Get total number of approved comments"""
        return obj.comments.filter(is_approved=True).count()

    def get_read_time(self, obj):
        """Calculate estimated reading time in minutes"""
        words = len(obj.content.split())
        minutes = max(1, words // 200)
        return minutes

    def get_user_has_liked(self, obj):
        """Check if current user has liked this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(post=obj, user=request.user).exists()
        return False


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating posts"""
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        required=False
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source='tags',
        many=True,
        required=False
    )

    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'content', 'excerpt', 'featured_image',
                  'category_id', 'tag_ids', 'status', 'is_featured', 'published_at']
        read_only_fields = ['id', 'slug']

    def validate_title(self, value):
        """Validate title is not empty and not too long"""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        if len(value) > 200:
            raise serializers.ValidationError("Title cannot exceed 200 characters.")
        return value

    def validate_content(self, value):
        """Validate content is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Content cannot be empty.")
        return value

    def validate(self, attrs):
        """Validate published_at is required when status is published"""
        status = attrs.get('status')
        published_at = attrs.get('published_at')

        if status == 'published' and not published_at:
            from django.utils import timezone
            attrs['published_at'] = timezone.now()

        return attrs

    def create(self, validated_data):
        """Create post with current user as author"""
        tags = validated_data.pop('tags', [])
        validated_data['author'] = self.context['request'].user
        post = Post.objects.create(**validated_data)

        if tags:
            post.tags.set(tags)

        return post

    def update(self, instance, validated_data):
        """Update post including tags"""
        tags = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        return instance


class LikeSerializer(serializers.ModelSerializer):
    """Serializer for Like model"""
    user = UserSerializer(read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'post', 'user', 'post_title', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def create(self, validated_data):
        """Create like with current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def validate(self, attrs):
        """Validate user hasn't already liked this post"""
        user = self.context['request'].user
        post = attrs.get('post')

        if Like.objects.filter(user=user, post=post).exists():
            raise serializers.ValidationError("You have already liked this post.")

        return attrs


class PostStatsSerializer(serializers.ModelSerializer):
    """Serializer for post statistics"""
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    comments_count = serializers.SerializerMethodField()
    views_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'likes_count', 'comments_count', 'views_count']

    def get_comments_count(self, obj):
        """Get total number of approved comments"""
        return obj.comments.filter(is_approved=True).count()
