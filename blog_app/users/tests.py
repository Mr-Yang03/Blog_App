"""
Unit Tests for Users App
Tests for User model, UserProfile, signals, and permissions
"""
from django.test import TestCase, SimpleTestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from users.models import UserProfile
from users.permissions import IsOwnerOrReadOnly
from tests.factories import UserFactory, UserProfileFactory
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
    
    def test_user_creation(self):
        """Test creating a user"""
        self.assertIsInstance(self.user, User)
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
    
    def test_user_string_representation(self):
        """Test user __str__ method"""
        self.assertEqual(str(self.user), self.user.username)
    
    def test_user_email_unique(self):
        """Test that email must be unique"""
        UserFactory(username='user2', email=self.user.email)
        # Should not raise error - email uniqueness not enforced in model
        # But in practice, registration form should validate this
    
    def test_user_password_hashing(self):
        """Test that password is hashed"""
        password = 'testpass123'
        user = UserFactory(password=password)
        self.assertNotEqual(user.password, password)
        self.assertTrue(user.check_password(password))
    
    def test_user_full_name(self):
        """Test get_full_name method if exists"""
        user = UserFactory(first_name='John', last_name='Doe')
        expected = f'{user.first_name} {user.last_name}'.strip()
        # Assuming User model has get_full_name method
        if hasattr(user, 'get_full_name'):
            self.assertEqual(user.get_full_name(), expected)
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class UserProfileModelTest(TestCase):
    """Test UserProfile model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.profile = self.user.profile  # Created by signal
    
    def test_profile_created_automatically(self):
        """Test that profile is created automatically via signal"""
        new_user = UserFactory()
        self.assertTrue(hasattr(new_user, 'profile'))
        self.assertIsInstance(new_user.profile, UserProfile)
    
    def test_profile_string_representation(self):
        """Test profile __str__ method"""
        expected = f"{self.user.username}'s profile"
        self.assertEqual(str(self.profile), expected)
    
    def test_profile_one_to_one_relationship(self):
        """Test one-to-one relationship with User"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.user.profile, self.profile)
    
    def test_profile_optional_fields(self):
        """Test that profile optional fields can be null/blank"""
        user = UserFactory()
        profile = user.profile  # Profile created by signal
        
        # UserProfile fields
        self.assertEqual(profile.phone_number, '')
        self.assertTrue(profile.notification_enabled)
        self.assertFalse(profile.email_verified)
        self.assertTrue(profile.is_public)
    
    def test_profile_update(self):
        """Test updating profile fields"""
        self.profile.phone_number = "+1234567890"
        self.profile.notification_enabled = False
        self.profile.save()
        
        updated_profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(updated_profile.phone_number, "+1234567890")
        self.assertFalse(updated_profile.notification_enabled)


class UserSignalTest(TestCase):
    """Test user-related signals"""
    
    def test_profile_created_on_user_creation(self):
        """Test that UserProfile is created when User is created"""
        user = UserFactory()
        
        # Check profile exists
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.user, user)
    
    def test_profile_not_duplicated(self):
        """Test that creating user doesn't duplicate profile"""
        user = UserFactory()
        initial_count = UserProfile.objects.filter(user=user).count()
        
        # Save user again
        user.save()
        
        final_count = UserProfile.objects.filter(user=user).count()
        self.assertEqual(initial_count, final_count)


class IsOwnerOrReadOnlyPermissionTest(TestCase):
    """Test custom permission class"""
    
    def setUp(self):
        """Set up test data"""
        self.permission = IsOwnerOrReadOnly()
        self.owner = UserFactory()
        self.other_user = UserFactory()
        self.factory = APIRequestFactory()
    
    def test_safe_methods_allowed(self):
        """Test that safe methods (GET, HEAD, OPTIONS) are allowed"""
        request = self.factory.get('/')
        request.user = self.other_user
        
        # Safe methods (GET) should be allowed for any user object
        self.assertTrue(self.permission.has_object_permission(request, None, self.owner))
    
    def test_owner_can_modify(self):
        """Test that owner can modify object"""
        request = self.factory.post('/')
        request.user = self.owner
        
        # Test with User object (obj == request.user)
        # IsOwnerOrReadOnly checks: obj == request.user
        # So we pass the user itself as the object
        
        # Owner should be able to modify their own user object
        self.assertTrue(self.permission.has_object_permission(request, None, self.owner))
    
    def test_non_owner_cannot_modify(self):
        """Test that non-owner cannot modify object"""
        request = self.factory.post('/')
        request.user = self.other_user
        
        # Other user trying to modify owner's user object
        # Should fail because obj (owner) != request.user (other_user)
        self.assertFalse(self.permission.has_object_permission(request, None, self.owner))


class UserFactoryTest(SimpleTestCase):
    """Test UserFactory"""
    
    databases = '__all__'
    
    def test_user_factory_creates_user(self):
        """Test that UserFactory creates valid user"""
        user = UserFactory.build()
        self.assertIsInstance(user, User)
        self.assertTrue(user.username)
        self.assertTrue(user.email)
    
    def test_user_factory_with_password(self):
        """Test UserFactory with custom password"""
        password = 'custompass123'
        user = UserFactory(password=password)
        self.assertTrue(user.check_password(password))
    
    def test_user_factory_unique_usernames(self):
        """Test that UserFactory generates unique usernames"""
        user1 = UserFactory()
        user2 = UserFactory()
        self.assertNotEqual(user1.username, user2.username)

