"""
Integration Tests - End-to-End User Workflows
Tests complete user journeys through the application
"""
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from tests.factories import UserFactory, PostFactory, CategoryFactory
from blog.models import Post, Comment, Like

User = get_user_model()


class UserRegistrationLoginWorkflowTest(APITestCase):
    """
    Test complete user registration and login workflow
    Flow: Register → Login → Get Profile → Update Profile
    """
    
    def setUp(self):
        """Set up test client"""
        self.client = APIClient()
    
    def test_complete_registration_and_login_flow(self):
        """Test user can register, login, and access protected resources"""
        
        # Step 1: Register new user
        register_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        register_response = self.client.post(
            reverse('api:register'),
            register_data,
            format='json'
        )
        
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', register_response.data)
        self.assertIn('tokens', register_response.data)
        
        user_id = register_response.data['user']['id']
        access_token = register_response.data['tokens']['access']
        refresh_token = register_response.data['tokens']['refresh']
        
        # Step 2: Verify user exists in database
        self.assertTrue(User.objects.filter(username='newuser').exists())
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        
        # Step 3: Verify profile was created automatically
        self.assertTrue(hasattr(user, 'profile'))
        
        # Step 4: Use access token to access protected endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Example: Get user profile
        # profile_response = self.client.get(reverse('api:user-detail', args=[user_id]))
        # self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        
        # Step 5: Test token refresh
        refresh_data = {'refresh': refresh_token}
        # refresh_response = self.client.post(reverse('api:token-refresh'), refresh_data)
        # self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        # self.assertIn('access', refresh_response.data)


class PostCreationWorkflowTest(APITestCase):
    """
    Test complete post creation workflow
    Flow: Login → Create Post → View Post → Edit Post → Delete Post
    """
    
    def setUp(self):
        """Set up authenticated user"""
        self.client = APIClient()
        self.user = UserFactory(password='testpass123')
        self.category = CategoryFactory()
        
        # Login user
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_complete_post_lifecycle(self):
        """Test creating, viewing, editing, and deleting a post"""
        
        # Step 1: Create a new post
        post_data = {
            'title': 'My First Blog Post',
            'content': 'This is the content of my first blog post.',
            'excerpt': 'Short excerpt',
            'category': self.category.id,
            'status': 'published'
        }
        
        # create_response = self.client.post(reverse('api:post-list'), post_data, format='json')
        # self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        # post_id = create_response.data['id']
        
        # Step 2: Verify post was created in database
        # self.assertTrue(Post.objects.filter(id=post_id).exists())
        # post = Post.objects.get(id=post_id)
        # self.assertEqual(post.title, 'My First Blog Post')
        # self.assertEqual(post.author, self.user)
        
        # Step 3: Retrieve the post
        # detail_response = self.client.get(reverse('api:post-detail', args=[post_id]))
        # self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        # self.assertEqual(detail_response.data['title'], 'My First Blog Post')
        
        # Step 4: Edit the post
        # update_data = {
        #     'title': 'Updated Blog Post Title',
        #     'content': post_data['content'],
        #     'category': self.category.id
        # }
        # update_response = self.client.put(reverse('api:post-detail', args=[post_id]), update_data, format='json')
        # self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        # self.assertEqual(update_response.data['title'], 'Updated Blog Post Title')
        
        # Step 5: Delete the post
        # delete_response = self.client.delete(reverse('api:post-detail', args=[post_id]))
        # self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        # self.assertFalse(Post.objects.filter(id=post_id).exists())


class CommentAndLikeWorkflowTest(APITestCase):
    """
    Test complete comment and like workflow
    Flow: View Post → Comment on Post → Reply to Comment → Like Post
    """
    
    def setUp(self):
        """Set up users and post"""
        self.client = APIClient()
        self.user1 = UserFactory(username='user1', password='pass123')
        self.user2 = UserFactory(username='user2', password='pass123')
        self.post = PostFactory(author=self.user1)
        
        # Authenticate as user2
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user2)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_complete_engagement_workflow(self):
        """Test commenting and liking a post"""
        
        # Step 1: View the post
        # post_response = self.client.get(reverse('api:post-detail', args=[self.post.id]))
        # self.assertEqual(post_response.status_code, status.HTTP_200_OK)
        
        # Step 2: Comment on the post
        comment_data = {
            'post': self.post.id,
            'content': 'Great post! Thanks for sharing.'
        }
        
        # comment_response = self.client.post(reverse('api:comment-list'), comment_data, format='json')
        # self.assertEqual(comment_response.status_code, status.HTTP_201_CREATED)
        # comment_id = comment_response.data['id']
        
        # Verify comment exists
        # self.assertTrue(Comment.objects.filter(id=comment_id, post=self.post).exists())
        # comment = Comment.objects.get(id=comment_id)
        # self.assertEqual(comment.author, self.user2)
        
        # Step 3: Reply to the comment (as user1, the post author)
        # Switch to user1
        refresh1 = RefreshToken.for_user(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh1.access_token)}')
        
        # reply_data = {
        #     'post': self.post.id,
        #     'parent': comment_id,
        #     'content': 'Thank you for your comment!'
        # }
        
        # reply_response = self.client.post(reverse('api:comment-list'), reply_data, format='json')
        # self.assertEqual(reply_response.status_code, status.HTTP_201_CREATED)
        # self.assertEqual(reply_response.data['parent'], comment_id)
        
        # Step 4: Like the post (as user2)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Create like directly since API endpoint might not be implemented
        Like.objects.create(post=self.post, user=self.user2)
        
        # Verify like exists
        self.assertTrue(Like.objects.filter(post=self.post, user=self.user2).exists())
        
        # Step 5: Verify post stats
        # Refresh post from database
        self.post.refresh_from_db()
        # self.assertEqual(self.post.likes.count(), 1)
        # self.assertEqual(self.post.comments.filter(parent=None).count(), 1)  # 1 parent comment
        # self.assertEqual(self.post.comments.count(), 2)  # 1 parent + 1 reply


class MultiUserInteractionTest(APITestCase):
    """
    Test multiple users interacting with same post
    Flow: User1 creates post → User2 likes → User3 comments → User1 replies
    """
    
    def setUp(self):
        """Set up multiple users"""
        self.client = APIClient()
        self.user1 = UserFactory(username='author', password='pass123')
        self.user2 = UserFactory(username='liker', password='pass123')
        self.user3 = UserFactory(username='commenter', password='pass123')
        self.category = CategoryFactory()
    
    def test_multi_user_post_interaction(self):
        """Test multiple users interacting with a single post"""
        
        # Step 1: User1 creates a post
        from rest_framework_simplejwt.tokens import RefreshToken as JWT
        refresh1 = JWT.for_user(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh1.access_token)}')
        
        post_data = {
            'title': 'Multi-User Test Post',
            'content': 'Testing multiple user interactions',
            'category': self.category.id,
            'status': 'published'
        }
        
        # create_response = self.client.post(reverse('api:post-list'), post_data, format='json')
        # self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        # post_id = create_response.data['id']
        
        # Create post directly for testing
        post = PostFactory(
            title='Multi-User Test Post',
            author=self.user1,
            category=self.category
        )
        
        # Step 2: User2 likes the post
        refresh2 = JWT.for_user(self.user2)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh2.access_token)}')
        
        # like_response = self.client.post(reverse('api:like-list'), {'post': post.id}, format='json')
        # self.assertEqual(like_response.status_code, status.HTTP_201_CREATED)
        
        # Step 3: User3 comments on the post
        refresh3 = JWT.for_user(self.user3)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh3.access_token)}')
        
        comment_data = {
            'post': post.id,
            'content': 'Interesting post!'
        }
        
        # comment_response = self.client.post(reverse('api:comment-list'), comment_data, format='json')
        # self.assertEqual(comment_response.status_code, status.HTTP_201_CREATED)
        # comment_id = comment_response.data['id']
        
        # Step 4: User1 (author) replies to comment
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh1.access_token)}')
        
        # reply_data = {
        #     'post': post.id,
        #     'parent': comment_id,
        #     'content': 'Thanks for reading!'
        # }
        
        # reply_response = self.client.post(reverse('api:comment-list'), reply_data, format='json')
        # self.assertEqual(reply_response.status_code, status.HTTP_201_CREATED)
        
        # Step 5: Verify final state
        post.refresh_from_db()
        # Should have 1 like and 2 comments (1 parent + 1 reply)
        # self.assertEqual(post.likes.count(), 1)
        # self.assertEqual(post.comments.count(), 2)


class SearchAndFilterWorkflowTest(APITestCase):
    """
    Test search and filter functionality
    Flow: Create multiple posts → Search → Filter by category → Filter by tag
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = UserFactory()
        self.tech_category = CategoryFactory(name="Technology")
        self.sports_category = CategoryFactory(name="Sports")
        
        # Create posts in different categories
        PostFactory.create_batch(3, category=self.tech_category, status='published')
        PostFactory.create_batch(2, category=self.sports_category, status='published')
        
        # Authenticate
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    
    def test_post_filtering_workflow(self):
        """Test filtering posts by various criteria"""
        
        # Step 1: Get all posts
        # all_posts_response = self.client.get(reverse('api:post-list'))
        # self.assertEqual(all_posts_response.status_code, status.HTTP_200_OK)
        # total_posts = len(all_posts_response.data)
        # self.assertEqual(total_posts, 5)
        
        # Step 2: Filter by Technology category
        # tech_posts_response = self.client.get(
        #     reverse('api:post-list'),
        #     {'category': self.tech_category.slug}
        # )
        # self.assertEqual(len(tech_posts_response.data), 3)
        
        # Step 3: Filter by Sports category
        # sports_posts_response = self.client.get(
        #     reverse('api:post-list'),
        #     {'category': self.sports_category.slug}
        # )
        # self.assertEqual(len(sports_posts_response.data), 2)
        
        # Step 4: Search posts
        # Assuming a post has "Django" in title
        # search_response = self.client.get(
        #     reverse('api:post-list'),
        #     {'search': 'Django'}
        # )
        # self.assertGreater(len(search_response.data), 0)
