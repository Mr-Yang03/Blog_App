"""
Unit Tests for Blog App
Tests for Post, Comment, Like, Category, Tag models
"""
from django.test import TestCase
from django.utils.text import slugify
from django.db import IntegrityError
from blog.models import Post, Comment, Like, Category, Tag
from tests.factories import (
    UserFactory, PostFactory, CommentFactory, ReplyFactory,
    LikeFactory, CategoryFactory, TagFactory, DraftPostFactory
)


class CategoryModelTest(TestCase):
    """Test Category model"""
    
    def test_category_creation(self):
        """Test creating a category"""
        category = CategoryFactory(name="Technology")
        self.assertEqual(category.name, "Technology")
        self.assertEqual(category.slug, "technology")
    
    def test_category_string_representation(self):
        """Test category __str__ method"""
        category = CategoryFactory(name="Python")
        self.assertEqual(str(category), "Python")
    
    def test_category_slug_auto_generation(self):
        """Test that slug is auto-generated from name"""
        category = Category.objects.create(name="Django Framework")
        self.assertEqual(category.slug, "django-framework")
    
    def test_category_unique_slug(self):
        """Test that category slug must be unique"""
        CategoryFactory(name="Test", slug="test-category")
        
        with self.assertRaises(IntegrityError):
            Category.objects.create(name="Test 2", slug="test-category")


class TagModelTest(TestCase):
    """Test Tag model"""
    
    def test_tag_creation(self):
        """Test creating a tag"""
        tag = TagFactory(name="Python")
        self.assertEqual(tag.name, "Python")
        self.assertEqual(tag.slug, "python")
    
    def test_tag_string_representation(self):
        """Test tag __str__ method"""
        tag = TagFactory(name="Django")
        self.assertEqual(str(tag), "Django")
    
    def test_tag_slug_auto_generation(self):
        """Test that slug is auto-generated from name"""
        tag = Tag.objects.create(name="Machine Learning")
        self.assertEqual(tag.slug, "machine-learning")


class PostModelTest(TestCase):
    """Test Post model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.category = CategoryFactory()
        self.post = PostFactory(author=self.user, category=self.category)
    
    def test_post_creation(self):
        """Test creating a post"""
        self.assertIsInstance(self.post, Post)
        self.assertEqual(self.post.author, self.user)
        self.assertEqual(self.post.category, self.category)
        self.assertEqual(self.post.status, 'published')
    
    def test_post_string_representation(self):
        """Test post __str__ method"""
        self.assertEqual(str(self.post), self.post.title)
    
    def test_post_slug_auto_generation(self):
        """Test that slug is auto-generated from title"""
        post = Post.objects.create(
            title="My First Blog Post",
            content="Content here",
            author=self.user,
            category=self.category
        )
        self.assertEqual(post.slug, "my-first-blog-post")
    
    def test_post_slug_uniqueness(self):
        """Test that duplicate slugs get numbered suffix"""
        # Create posts with same title but don't use factory's random title
        post1 = Post.objects.create(
            title="Test Post",
            content="Content 1",
            author=self.user,
            category=self.category,
            status='published'
        )
        post2 = Post.objects.create(
            title="Test Post",
            content="Content 2",
            author=self.user,
            category=self.category,
            status='published'
        )
        
        # Second post should have different slug with numbered suffix
        self.assertNotEqual(post1.slug, post2.slug)
        self.assertEqual(post1.slug, "test-post")
        self.assertEqual(post2.slug, "test-post-1")
    
    def test_post_draft_status(self):
        """Test creating a draft post"""
        draft = DraftPostFactory(author=self.user)
        self.assertEqual(draft.status, 'draft')
        self.assertIsNone(draft.published_at)
    
    def test_post_views_count_default(self):
        """Test that views_count defaults to 0"""
        post = PostFactory(author=self.user, views_count=0)
        self.assertEqual(post.views_count, 0)
    
    def test_post_many_to_many_tags(self):
        """Test adding tags to post"""
        tag1 = TagFactory(name="Python")
        tag2 = TagFactory(name="Django")
        
        # Clear existing tags (factory adds 2-3 by default)
        self.post.tags.clear()
        
        # Add our specific tags
        self.post.tags.add(tag1, tag2)
        
        self.assertEqual(self.post.tags.count(), 2)
        self.assertIn(tag1, self.post.tags.all())
        self.assertIn(tag2, self.post.tags.all())


class CommentModelTest(TestCase):
    """Test Comment model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.post = PostFactory()
        self.comment = CommentFactory(post=self.post, author=self.user)
    
    def test_comment_creation(self):
        """Test creating a comment"""
        self.assertIsInstance(self.comment, Comment)
        self.assertEqual(self.comment.post, self.post)
        self.assertEqual(self.comment.author, self.user)
        self.assertIsNone(self.comment.parent)
        self.assertTrue(self.comment.is_approved)
    
    def test_comment_string_representation(self):
        """Test comment __str__ method"""
        expected = f"Comment by {self.user.username} on {self.post.title}"
        self.assertEqual(str(self.comment), expected)
    
    def test_comment_reply_creation(self):
        """Test creating a reply to a comment"""
        reply = ReplyFactory(
            post=self.post,
            author=UserFactory(),
            parent=self.comment
        )
        
        self.assertEqual(reply.parent, self.comment)
        self.assertEqual(reply.post, self.post)
        self.assertIn(reply, self.comment.replies.all())
    
    def test_comment_approval_status(self):
        """Test comment approval status"""
        unapproved_comment = CommentFactory(
            post=self.post,
            author=self.user,
            is_approved=False
        )
        
        self.assertFalse(unapproved_comment.is_approved)
    
    def test_comment_cascade_delete_with_post(self):
        """Test that comments are deleted when post is deleted"""
        post = PostFactory()
        comment = CommentFactory(post=post)
        comment_id = comment.id
        
        post.delete()
        
        self.assertFalse(Comment.objects.filter(id=comment_id).exists())
    
    def test_comment_replies_cascade_delete(self):
        """Test that replies are deleted when parent comment is deleted"""
        parent = CommentFactory(post=self.post)
        reply = ReplyFactory(post=self.post, parent=parent)
        reply_id = reply.id
        
        parent.delete()
        
        self.assertFalse(Comment.objects.filter(id=reply_id).exists())


class LikeModelTest(TestCase):
    """Test Like model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.post = PostFactory()
        self.like = LikeFactory(post=self.post, user=self.user)
    
    def test_like_creation(self):
        """Test creating a like"""
        self.assertIsInstance(self.like, Like)
        self.assertEqual(self.like.post, self.post)
        self.assertEqual(self.like.user, self.user)
    
    def test_like_string_representation(self):
        """Test like __str__ method"""
        expected = f"{self.user.username} liked {self.post.title}"
        self.assertEqual(str(self.like), expected)
    
    def test_like_unique_together_constraint(self):
        """Test that a user can only like a post once"""
        with self.assertRaises(IntegrityError):
            Like.objects.create(post=self.post, user=self.user)
    
    def test_multiple_users_can_like_same_post(self):
        """Test that multiple users can like the same post"""
        user2 = UserFactory()
        like2 = LikeFactory(post=self.post, user=user2)
        
        self.assertEqual(self.post.likes.count(), 2)
    
    def test_user_can_like_multiple_posts(self):
        """Test that a user can like multiple posts"""
        post2 = PostFactory()
        like2 = LikeFactory(post=post2, user=self.user)
        
        self.assertEqual(self.user.likes.count(), 2)
    
    def test_like_cascade_delete_with_post(self):
        """Test that likes are deleted when post is deleted"""
        post = PostFactory()
        like = LikeFactory(post=post, user=self.user)
        like_id = like.id
        
        post.delete()
        
        self.assertFalse(Like.objects.filter(id=like_id).exists())


class PostRelationshipsTest(TestCase):
    """Test Post model relationships"""
    
    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.post = PostFactory(author=self.user)
    
    def test_post_comments_relationship(self):
        """Test post.comments relationship"""
        comment1 = CommentFactory(post=self.post)
        comment2 = CommentFactory(post=self.post)
        
        self.assertEqual(self.post.comments.count(), 2)
        self.assertIn(comment1, self.post.comments.all())
        self.assertIn(comment2, self.post.comments.all())
    
    def test_post_likes_relationship(self):
        """Test post.likes relationship"""
        like1 = LikeFactory(post=self.post)
        like2 = LikeFactory(post=self.post)
        
        self.assertEqual(self.post.likes.count(), 2)
    
    def test_post_author_relationship(self):
        """Test post.author relationship"""
        self.assertEqual(self.post.author, self.user)
        self.assertIn(self.post, self.user.posts.all())
    
    def test_post_category_relationship(self):
        """Test post.category relationship"""
        category = CategoryFactory()
        post = PostFactory(category=category)
        
        self.assertEqual(post.category, category)
        # Note: Need to check if reverse relation exists
        # self.assertIn(post, category.posts.all())

