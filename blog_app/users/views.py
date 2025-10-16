from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import User, UserProfile

# Create your views here.

def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('blog:home')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')

        # Validation
        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'users/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'users/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'users/register.html')

        # Create user
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                # Create user profile
                UserProfile.objects.create(user=user)

            messages.success(request, 'Account created successfully! Please login.')
            return redirect('users:login')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')

    return render(request, 'users/register.html')


def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('blog:home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'blog:home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'users/login.html')


@login_required
def user_logout(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('blog:home')


@login_required
def profile(request, username):
    """User profile view"""
    profile_user = get_object_or_404(User, username=username)

    # Get user's posts
    posts = profile_user.posts.filter(status='published').order_by('-published_at')

    # Get user's comments count
    comments_count = profile_user.comments.count()

    # Get user's likes count
    likes_count = profile_user.likes.count()

    context = {
        'profile_user': profile_user,
        'posts': posts,
        'posts_count': posts.count(),
        'comments_count': comments_count,
        'likes_count': likes_count,
    }
    return render(request, 'users/profile.html', context)


@login_required
def edit_profile(request):
    """Edit user profile"""
    user = request.user

    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        # Update user fields
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', user.email)
        user.bio = request.POST.get('bio', '')
        user.website = request.POST.get('website', '')
        user.location = request.POST.get('location', '')

        # Handle avatar upload
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']

        user.save()

        # Update profile fields
        profile.phone_number = request.POST.get('phone_number', '')
        profile.notification_enabled = request.POST.get('notification_enabled') == 'on'
        profile.is_public = request.POST.get('is_public') == 'on'
        profile.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('users:profile', username=user.username)

    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'users/edit_profile.html', context)
