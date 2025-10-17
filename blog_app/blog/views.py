from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib import messages
from django.utils import timezone
from django.utils.text import slugify
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


@login_required
def create_post(request):
    """Create a new blog post"""
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        excerpt = request.POST.get('excerpt')
        category_id = request.POST.get('category')
        tag_ids = request.POST.getlist('tags')
        status = request.POST.get('status', 'draft')
        is_featured = request.POST.get('is_featured') == 'on'
        featured_image = request.FILES.get('featured_image')

        if title and content:
            # Generate unique slug
            slug = slugify(title)
            original_slug = slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1

            # Create post
            post = Post.objects.create(
                title=title,
                slug=slug,
                author=request.user,
                content=content,
                excerpt=excerpt,
                category_id=category_id if category_id else None,
                status=status,
                is_featured=is_featured,
                featured_image=featured_image,
                published_at=timezone.now() if status == 'published' else None
            )

            # Add tags
            if tag_ids:
                post.tags.set(tag_ids)

            messages.success(request, 'Post created successfully!')
            return redirect('blog:post_detail', slug=post.slug)
        else:
            messages.error(request, 'Title and content are required.')

    categories = Category.objects.all()
    tags = Tag.objects.all()
    context = {
        'categories': categories,
        'tags': tags,
    }
    return render(request, 'blog/create_post.html', context)


@login_required
def edit_post(request, slug):
    """Edit an existing blog post"""
    post = get_object_or_404(Post, slug=slug)

    # Check if user is the author
    if post.author != request.user:
        messages.error(request, 'You do not have permission to edit this post.')
        return redirect('blog:post_detail', slug=post.slug)

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        excerpt = request.POST.get('excerpt')
        category_id = request.POST.get('category')
        tag_ids = request.POST.getlist('tags')
        status = request.POST.get('status', 'draft')
        is_featured = request.POST.get('is_featured') == 'on'
        featured_image = request.FILES.get('featured_image')

        if title and content:
            # Update slug if title changed
            if post.title != title:
                slug = slugify(title)
                original_slug = slug
                counter = 1
                while Post.objects.filter(slug=slug).exclude(id=post.id).exists():
                    slug = f"{original_slug}-{counter}"
                    counter += 1
                post.slug = slug

            post.title = title
            post.content = content
            post.excerpt = excerpt
            post.category_id = category_id if category_id else None
            post.status = status
            post.is_featured = is_featured

            # Update published_at when status changes to published
            if status == 'published' and not post.published_at:
                post.published_at = timezone.now()

            if featured_image:
                post.featured_image = featured_image

            post.save()

            # Update tags
            if tag_ids:
                post.tags.set(tag_ids)
            else:
                post.tags.clear()

            messages.success(request, 'Post updated successfully!')
            return redirect('blog:post_detail', slug=post.slug)
        else:
            messages.error(request, 'Title and content are required.')

    categories = Category.objects.all()
    tags = Tag.objects.all()
    context = {
        'post': post,
        'categories': categories,
        'tags': tags,
    }
    return render(request, 'blog/edit_post.html', context)


@login_required
def delete_post(request, slug):
    """Delete a blog post"""
    post = get_object_or_404(Post, slug=slug)

    # Check if user is the author
    if post.author != request.user:
        messages.error(request, 'You do not have permission to delete this post.')
        return redirect('blog:post_detail', slug=post.slug)

    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('blog:home')

    return redirect('blog:post_detail', slug=post.slug)


@login_required
def my_posts(request):
    """View all posts by the logged-in user"""
    posts = Post.objects.filter(author=request.user).order_by('-created_at')

    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        posts = posts.filter(status=status_filter)

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
    }
    return render(request, 'blog/my_posts.html', context)
