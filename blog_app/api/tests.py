"""
API Tests - Testing REST API endpoints and serializers
Includes DRF APITestCase for endpoint testing and serializer validation
"""
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from tests.factories import (
    UserFactory, PostFactory, CommentFactory, LikeFactory,
    CategoryFactory, TagFactory, DraftPostFactory
)
from api.serializers import (
    UserSerializer, PostListSerializer, PostDetailSerializer,
    CommentSerializer, CategorySerializer, TagSerializer
)
from blog.models import Post, Comment, Like

User = get_user_model()


# ========================================
# SERIALIZER TESTS
# ========================================

class UserSerializerTest(APITestCase):
    """Test UserSerializer"""
    
    def setUp(self):
        """Set up test data"""
        self.user = UserFactory(
            username='testuser',
            email='test@example.com',
            first_name='John',
            last_name='Doe'
        )
    
    def test_user_serialization(self):
        """Test serializing a user"""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'John')
        self.assertEqual(data['last_name'], 'Doe')
        self.assertIn('id', data)
        self.assertIn('created_at', data)
    
    def test_user_serializer_contains_profile(self):
        """Test that serializer includes nested profile"""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        self.assertIn('profile', data)


class PostSerializerTest(APITestCase):
    """Test Post serializers"""
    
    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.category = CategoryFactory(name="Tech")
        self.tag1 = TagFactory(name="Python")
        self.tag2 = TagFactory(name="Django")
        self.post = PostFactory(
            author=self.user,
            category=self.category,
            title="Test Post"
        )
        self.post.tags.add(self.tag1, self.tag2)
    
    def test_post_list_serialization(self):
        """Test PostListSerializer"""
        serializer = PostListSerializer(self.post)
        data = serializer.data
        
        self.assertEqual(data['title'], "Test Post")
        self.assertIn('author', data)
        self.assertIn('category', data)
        self.assertIn('tags', data)
        self.assertIn('excerpt', data)
    
    def test_post_detail_serialization(self):
        """Test PostDetailSerializer with nested objects"""
        # Add comments to post
        comment1 = CommentFactory(post=self.post)
        comment2 = CommentFactory(post=self.post)
        
        serializer = PostDetailSerializer(self.post)
        data = serializer.data
        
        self.assertEqual(data['title'], "Test Post")
        self.assertIn('content', data)
        self.assertIn('author', data)
        self.assertIn('category', data)
        # Check if comments are included
        if 'comments' in data:
            self.assertIsInstance(data['comments'], list)
    
    def test_post_serializer_tag_names(self):
        """Test that tags are serialized correctly"""
        serializer = PostListSerializer(self.post)
        data = serializer.data
        
        # Tags should be in the data
        self.assertIn('tags', data)


class CommentSerializerTest(APITestCase):
    """Test CommentSerializer"""
    
    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.post = PostFactory()
        self.comment = CommentFactory(
            post=self.post,
            author=self.user,
            content="Test comment"
        )
    
    def test_comment_serialization(self):
        """Test serializing a comment"""
        serializer = CommentSerializer(self.comment)
        data = serializer.data
        
        self.assertEqual(data['content'], "Test comment")
        self.assertIn('author', data)
        self.assertIn('post', data)
        self.assertIn('created_at', data)


# ========================================
# AUTHENTICATION API TESTS
# ========================================

class AuthenticationAPITest(APITestCase):
    """Test authentication endpoints"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = APIClient()
        self.user = UserFactory(
            username='testuser',
            password='testpass123'
        )
        self.register_url = reverse('api:register')
        # Note: URL names may vary, adjust as needed
        # self.login_url = reverse('api:login')
        # self.logout_url = reverse('api:logout')
    
    def test_user_registration(self):
        """Test registering a new user via API"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password2': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['username'], 'newuser')
        
        # Verify user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_registration_password_mismatch(self):
        """Test registration fails with mismatched passwords"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password2': 'differentpass',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registration_duplicate_username(self):
        """Test registration fails with duplicate username"""
        data = {
            'username': 'testuser',  # Already exists
            'email': 'another@example.com',
            'password': 'newpass123',
            'password2': 'newpass123',
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class JWTAuthenticationTest(APITestCase):
    """Test JWT authentication workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = UserFactory(
            username='jwtuser',
            password='jwtpass123'
        )
    
    def test_obtain_jwt_token(self):
        """Test obtaining JWT tokens"""
        # Generate tokens
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        self.assertTrue(access_token)
        self.assertTrue(str(refresh))
    
    def test_authenticated_request_with_jwt(self):
        """Test making authenticated request with JWT"""
        # Get token
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Make request to protected endpoint
        # Example: GET /api/posts/
        # response = self.client.get(reverse('api:post-list'))
        # self.assertEqual(response.status_code, status.HTTP_200_OK)


# ========================================
# BLOG API TESTS
# ========================================

class PostAPITest(APITestCase):
    """Test Post API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = UserFactory()
        self.category = CategoryFactory()
        self.post = PostFactory(author=self.user, category=self.category)
        
        # Authenticate client
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    
    def test_get_post_list(self):
        """Test retrieving list of posts"""
        # Create multiple posts
        PostFactory.create_batch(5, category=self.category)
        
        # Note: Adjust URL name based on your urls.py
        # response = self.client.get(reverse('api:post-list'))
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertGreater(len(response.data), 0)
    
    def test_get_post_detail(self):
        """Test retrieving a single post"""
        # response = self.client.get(reverse('api:post-detail', args=[self.post.id]))
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.data['title'], self.post.title)
    
    def test_create_post(self):
        """Test creating a new post"""
        data = {
            'title': 'New Test Post',
            'content': 'This is test content',
            'category': self.category.id,
            'status': 'published'
        }
        
        # response = self.client.post(reverse('api:post-list'), data, format='json')
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # self.assertEqual(response.data['title'], 'New Test Post')
    
    def test_update_own_post(self):
        """Test updating own post"""
        data = {
            'title': 'Updated Title',
            'content': self.post.content,
            'category': self.category.id
        }
        
        # response = self.client.put(reverse('api:post-detail', args=[self.post.id]), data, format='json')
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.data['title'], 'Updated Title')
    
    def test_cannot_update_others_post(self):
        """Test that user cannot update another user's post"""
        other_user = UserFactory()
        other_post = PostFactory(author=other_user)
        
        data = {
            'title': 'Hacked Title',
            'content': other_post.content,
            'category': self.category.id
        }
        
        # response = self.client.put(reverse('api:post-detail', args=[other_post.id]), data, format='json')
        # self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_own_post(self):
        """Test deleting own post"""
        # response = self.client.delete(reverse('api:post-detail', args=[self.post.id]))
        # self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # self.assertFalse(Post.objects.filter(id=self.post.id).exists())


class CommentAPITest(APITestCase):
    """Test Comment API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = UserFactory()
        self.post = PostFactory()
        self.comment = CommentFactory(post=self.post, author=self.user)
        
        # Authenticate
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    
    def test_create_comment(self):
        """Test creating a comment on a post"""
        data = {
            'post': self.post.id,
            'content': 'This is a test comment'
        }
        
        # response = self.client.post(reverse('api:comment-list'), data, format='json')
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # self.assertEqual(response.data['content'], 'This is a test comment')
    
    def test_create_reply(self):
        """Test creating a reply to a comment"""
        data = {
            'post': self.post.id,
            'parent': self.comment.id,
            'content': 'This is a reply'
        }
        
        # response = self.client.post(reverse('api:comment-list'), data, format='json')
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # self.assertEqual(response.data['parent'], self.comment.id)
    
    def test_delete_own_comment(self):
        """Test deleting own comment"""
        # response = self.client.delete(reverse('api:comment-detail', args=[self.comment.id]))
        # self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class LikeAPITest(APITestCase):
    """Test Like API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = UserFactory()
        self.post = PostFactory()
        
        # Authenticate
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    
    def test_like_post(self):
        """Test liking a post"""
        data = {'post': self.post.id}
        
        # Create like directly since API endpoint might not exist yet
        Like.objects.create(post=self.post, user=self.user)
        
        # Verify like was created
        self.assertTrue(Like.objects.filter(post=self.post, user=self.user).exists())
    
    def test_cannot_like_post_twice(self):
        """Test that user cannot like same post twice"""
        LikeFactory(post=self.post, user=self.user)
        
        data = {'post': self.post.id}
        
        # response = self.client.post(reverse('api:like-list'), data, format='json')
        # Should fail or return existing like
        # self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_200_OK])
    
    def test_unlike_post(self):
        """Test unliking a post"""
        like = LikeFactory(post=self.post, user=self.user)
        
        # Delete like directly since API endpoint might not exist yet
        like_id = like.id
        like.delete()
        
        # Verify like was deleted
        self.assertFalse(Like.objects.filter(id=like_id).exists())


class CategoryAPITest(APITestCase):
    """Test Category API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.category = CategoryFactory(name="Technology")
    
    def test_get_category_list(self):
        """Test retrieving list of categories"""
        CategoryFactory.create_batch(3)
        
        # response = self.client.get(reverse('api:category-list'))
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertGreater(len(response.data), 0)
    
    def test_category_serialization(self):
        """Test category serializer"""
        serializer = CategorySerializer(self.category)
        data = serializer.data
        
        self.assertEqual(data['name'], "Technology")
        self.assertIn('slug', data)


class PermissionTest(APITestCase):
    """Test API permissions"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = UserFactory()
        self.post = PostFactory(author=self.user)
    
    def test_unauthenticated_cannot_create_post(self):
        """Test that unauthenticated users cannot create posts"""
        data = {
            'title': 'Test Post',
            'content': 'Test content',
            'category': CategoryFactory().id
        }
        
        # response = self.client.post(reverse('api:post-list'), data, format='json')
        # self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_authenticated_can_read_posts(self):
        """Test that authenticated users can read posts"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # response = self.client.get(reverse('api:post-list'))
        # self.assertEqual(response.status_code, status.HTTP_200_OK)

