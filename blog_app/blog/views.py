from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib import messages
from .models import Post, Comment, Like, Category, Tag

# Create your views here.

def home(request):
    """Home page with featured posts"""
    featured_posts = Post.objects.filter(status='published', is_featured=True).order_by('-published_at')[:3]
    recent_posts = Post.objects.filter(status='published').order_by('-published_at')[:6]
    categories = Category.objects.all()

    context = {
        'featured_posts': featured_posts,
        'recent_posts': recent_posts,
        'categories': categories,
    }
    return render(request, 'blog/home.html', context)


def post_list(request):
    """List all published posts with pagination and filtering"""
    posts = Post.objects.filter(status='published').order_by('-published_at')

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(author__username__icontains=search_query)
        )

    # Category filter
    category_slug = request.GET.get('category')
    if category_slug:
        posts = posts.filter(category__slug=category_slug)

    # Tag filter
    tag_slug = request.GET.get('tag')
    if tag_slug:
        posts = posts.filter(tags__slug=tag_slug)

    # Pagination
    paginator = Paginator(posts, 9)  # 9 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'categories': Category.objects.all(),
        'popular_tags': Tag.objects.annotate(post_count=Count('posts')).order_by('-post_count')[:10],
    }
    return render(request, 'blog/post_list.html', context)


def post_detail(request, slug):
    """Detail view for a single post"""
    post = get_object_or_404(Post, slug=slug, status='published')

    # Increment views count
    post.views_count += 1
    post.save(update_fields=['views_count'])

    # Get comments
    comments = post.comments.filter(parent=None, is_approved=True).order_by('-created_at')

    # Check if user liked the post
    user_liked = False
    if request.user.is_authenticated:
        user_liked = Like.objects.filter(post=post, user=request.user).exists()

    # Get related posts
    related_posts = Post.objects.filter(
        category=post.category,
        status='published'
    ).exclude(id=post.id)[:3]

    context = {
        'post': post,
        'comments': comments,
        'user_liked': user_liked,
        'related_posts': related_posts,
        'likes_count': post.likes.count(),
        'comments_count': post.comments.filter(is_approved=True).count(),
    }
    return render(request, 'blog/post_detail.html', context)


@login_required
def add_comment(request, post_slug):
    """Add a comment to a post"""
    if request.method == 'POST':
        post = get_object_or_404(Post, slug=post_slug, status='published')
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')

        if content:
            comment = Comment.objects.create(
                post=post,
                author=request.user,
                content=content,
                parent_id=parent_id if parent_id else None
            )
            messages.success(request, 'Comment added successfully!')
        else:
            messages.error(request, 'Comment content cannot be empty.')

    return redirect('blog:post_detail', slug=post_slug)


@login_required
def toggle_like(request, post_slug):
    """Toggle like on a post"""
    post = get_object_or_404(Post, slug=post_slug, status='published')

    like, created = Like.objects.get_or_create(post=post, user=request.user)

    if not created:
        like.delete()
        messages.info(request, 'Post unliked.')
    else:
        messages.success(request, 'Post liked!')

    return redirect('blog:post_detail', slug=post_slug)


def category_posts(request, slug):
    """Posts filtered by category"""
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(category=category, status='published').order_by('-published_at')

    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'blog/category_posts.html', context)


def tag_posts(request, slug):
    """Posts filtered by tag"""
    tag = get_object_or_404(Tag, slug=slug)
    posts = Post.objects.filter(tags=tag, status='published').order_by('-published_at')

    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'tag': tag,
        'page_obj': page_obj,
    }
    return render(request, 'blog/tag_posts.html', context)
