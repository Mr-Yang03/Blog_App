"""
Factory Boy Factories for Testing
Creates realistic test data for all models
"""
import factory
from factory.django import DjangoModelFactory
from django.utils.text import slugify
from django.utils import timezone
from users.models import User, UserProfile
from blog.models import Post, Comment, Like, Category, Tag


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances"""
    
    class Meta:
        model = User
        django_get_or_create = ('username',)
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Set password after user creation"""
        if not create:
            return
        
        if extracted:
            self.set_password(extracted)
        else:
            self.set_password('testpass123')


class UserProfileFactory(DjangoModelFactory):
    """Factory for creating UserProfile instances"""
    
    class Meta:
        model = UserProfile
    
    user = factory.SubFactory(UserFactory)
    bio = factory.Faker('text', max_nb_chars=200)
    location = factory.Faker('city')
    website = factory.Faker('url')
    birth_date = factory.Faker('date_of_birth', minimum_age=18, maximum_age=80)
    # avatar = factory.django.ImageField(color='blue')


class CategoryFactory(DjangoModelFactory):
    """Factory for creating Category instances"""
    
    class Meta:
        model = Category
        django_get_or_create = ('slug',)
    
    name = factory.Sequence(lambda n: f'Category {n}')
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    description = factory.Faker('text', max_nb_chars=150)


class TagFactory(DjangoModelFactory):
    """Factory for creating Tag instances"""
    
    class Meta:
        model = Tag
        django_get_or_create = ('slug',)
    
    name = factory.Sequence(lambda n: f'Tag {n}')
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))


class PostFactory(DjangoModelFactory):
    """Factory for creating Post instances"""
    
    class Meta:
        model = Post
    
    title = factory.Faker('sentence', nb_words=6)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    content = factory.Faker('text', max_nb_chars=1000)
    excerpt = factory.Faker('text', max_nb_chars=200)
    author = factory.SubFactory(UserFactory)
    category = factory.SubFactory(CategoryFactory)
    status = 'published'
    is_featured = False
    published_at = factory.LazyFunction(timezone.now)
    views_count = factory.Faker('random_int', min=0, max=1000)
    
    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """Add tags to post"""
        if not create:
            return
        
        if extracted:
            for tag in extracted:
                self.tags.add(tag)
        else:
            # Add 2-3 random tags by default
            import random
            num_tags = random.randint(2, 3)
            for _ in range(num_tags):
                self.tags.add(TagFactory())


class CommentFactory(DjangoModelFactory):
    """Factory for creating Comment instances"""
    
    class Meta:
        model = Comment
    
    post = factory.SubFactory(PostFactory)
    author = factory.SubFactory(UserFactory)
    parent = None  # Top-level comment by default
    content = factory.Faker('text', max_nb_chars=300)
    is_approved = True


class ReplyFactory(CommentFactory):
    """Factory for creating Reply (child comment) instances"""
    
    parent = factory.SubFactory(CommentFactory)


class LikeFactory(DjangoModelFactory):
    """Factory for creating Like instances"""
    
    class Meta:
        model = Like
    
    post = factory.SubFactory(PostFactory)
    user = factory.SubFactory(UserFactory)


# Specialized Factories

class DraftPostFactory(PostFactory):
    """Factory for draft posts"""
    status = 'draft'
    published_at = None


class FeaturedPostFactory(PostFactory):
    """Factory for featured posts"""
    is_featured = True


class StaffUserFactory(UserFactory):
    """Factory for staff users"""
    is_staff = True


class SuperUserFactory(UserFactory):
    """Factory for superusers"""
    is_staff = True
    is_superuser = True
