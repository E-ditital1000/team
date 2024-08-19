from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, auth
from django.contrib import messages
from .forms import BlogPostForm, CommentForm
from .models import Blog_Post
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from .models import UserProfile
from django.utils import timezone
from datetime import timedelta
from .models import Blog_Post, Comment, Category
from .forms import CommentForm
import logging
from django.views.decorators.http import require_POST

class ProfileEditView(UpdateView):
    model = UserProfile
    fields = ['bio', 'profile_picture']
    template_name = 'profile_edit.html'
    success_url = reverse_lazy('profile_edit')

    def get_object(self):
        return self.request.user.userprofile
    
def about(request):
    return render(request, 'about.html')

@login_required
def edit_profile(request):
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)

    if request.method == 'POST':
        # Handle form submission
        pass

    return render(request, 'profile/edit.html', {'user_profile': user_profile})

@login_required
def edit_profile(request):
    try:
        user_profile = request.user.userprofile
    except ObjectDoesNotExist:
        return redirect('create_user_profile')  # Redirect to a view to create a UserProfile

    if request.method == 'POST':
        # Handle form submission
        pass

    return render(request, 'profile/edit.html', {'user_profile': user_profile})
    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()


# Register User
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, 'Passwords must match.')
            return redirect('register')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already in use.')
            return redirect('register')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already in use.')
            return redirect('register')

        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, 'Your account has been created! You can now log in.')
        return redirect('login')
    return render(request, 'register.html')

from django.db import IntegrityError, transaction


def create_blog_post(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.writer = request.user
            try:
                with transaction.atomic():
                    # Attempt to save the blog post within a transaction
                    post.save()
                    # Save many-to-many data for the form
                    form.save_m2m()
                messages.success(request, 'Blog post created successfully.')
                return redirect('index')  # Assuming 'index' is your correct redirect destination
            except IntegrityError as e:
                logger.error(f"IntegrityError while creating post: {post.title} by user {request.user.username}. Error: {e}")
                # Handle slug collision by regenerating slug
                post.slug = None  # Reset slug to trigger regeneration
                try:
                    with transaction.atomic():
                        post.save()
                        form.save_m2m()
                    messages.success(request, 'Blog post created successfully with an adjusted slug.')
                    logger.info(f"Post {post.title} created with adjusted slug {post.slug}.")
                    return redirect('index')
                except IntegrityError as e:
                    logger.critical(f"Failed to create post {post.title} even after adjusting slug: {e}")
                    messages.error(request, 'Failed to create the blog post due to a critical error.')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = BlogPostForm()

    return render(request, 'create_blog_post.html', {'form': form})

@login_required
@require_POST
def like_post(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        post_id = request.POST.get('post_id')
        print(f"Received post_id: {post_id}")
        post = get_object_or_404(Blog_Post, id=post_id)
        user = request.user
        print(f"User: {user.username} is liking post {post.title}")

        if post.likes.filter(id=user.id).exists():
            post.likes.remove(user)
            liked = False
            print(f"Post {post.title} unliked by {user.username}")
        else:
            post.likes.add(user)
            liked = True
            print(f"Post {post.title} liked by {user.username}")

        return JsonResponse({
            'liked': liked,
            'total_likes': post.total_likes(),
            'post_id': post_id
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

logger = logging.getLogger(__name__)

@login_required
def edit_blog_post(request, slug):
    blog_post = get_object_or_404(Blog_Post, slug=slug)
    if blog_post.writer != request.user:
        messages.error(request, "You are not authorized to edit this post.")
        logger.warning(f"Unauthorized edit attempt by user {request.user} on post {slug}")
        return redirect('blog_detail', slug=slug)
    
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=blog_post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Blog post updated successfully.')
            return redirect('blog_detail', slug=blog_post.slug)
    else:
        form = BlogPostForm(instance=blog_post)
    
    return render(request, 'edit_blog_post.html', {'form': form})

logger = logging.getLogger(__name__)
@login_required
def delete_blog_post(request, slug):
    blog_post = get_object_or_404(Blog_Post, slug=slug)
    if blog_post.writer != request.user:
        messages.error(request, "You are not authorized to delete this post.")
        logger.warning(f"Unauthorized delete attempt by user {request.user} on post {slug}")
        return redirect('blog_detail', slug=slug)

    if request.method == 'POST':
        blog_post.delete()
        messages.success(request, "Blog post deleted successfully.")
        return redirect('index')

    return render(request, 'delete_blog_post.html', {'blog_post': blog_post})

# Login and Logout Handlers
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)
        if user:
            auth.login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Invalid credentials.')
            return redirect('login')
    return render(request, 'login.html')

logger = logging.getLogger(__name__)

def delete_blog_post(request, slug):
    posts = Blog_Post.objects.filter(slug=slug)
    if posts.count() == 1:
        post = posts.first()
        # proceed with deletion logic
    elif posts.count() > 1:
        logger.error(f"Multiple Blog_Post entries with the same slug '{slug}' found.")
        # handle error
    else:
        logger.warning(f"No Blog_Post found for the slug '{slug}'.")
        # handle no post found


def logout(request):
    auth.logout(request)
    return redirect('index')

# Search, Index, and Detailed Views
def search_results(request):
    query = request.GET.get('query')
    results = Blog_Post.objects.filter(title__icontains=query)
    return render(request, 'search_results.html', {'query': query, 'results': results})

def index(request):
    posts = Blog_Post.objects.all()
    return render(request, 'index.html', {'posts': posts})

def category_detail_view(request, slug):
    category = Category.objects.get(slug=slug)
    posts = category.blog_post_set.all()  # This depends on your related_name in Blog_Post model
    return render(request, 'category_detail.html', {'category': category, 'posts': posts})


@login_required(login_url='login/')
def blog_detail_view(request, slug):
    post = get_object_or_404(Blog_Post, slug=slug)
    
    # Increment the view count only if it's a new view for this user
    new_view = post.increment_view_count(request.user)

    # Fetch recent posts from the last 10 days
    now = timezone.now()
    date_from = now - timedelta(days=10)
    recent_posts = Blog_Post.objects.filter(created_on__gte=date_from).order_by('-created_on')[:3]

    comments = post.comments.filter(parent__isnull=True).prefetch_related('replies')
    
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.commenter = request.user  # Set the commenter to the current user
            parent_id = request.POST.get('parent_id')
            if parent_id:
                new_comment.parent = Comment.objects.get(id=parent_id)
            new_comment.save()
            return redirect('blog_detail', slug=post.slug)
    else:
        comment_form = CommentForm()

    return render(request, 'blog_detail.html', {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'recent_posts': recent_posts,
        'user': request.user,
        'new_view': new_view,  # Added this to indicate if it's a new view
    })



from django.contrib.auth.decorators import user_passes_test


def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
def set_cookie_view(request):
    response = HttpResponse("Cookie Set")
    response.set_cookie('my_cookie', 'cookie_value')
    return response

@user_passes_test(is_superuser)
def get_cookie_view(request):
    cookie_value = request.COOKIES.get('my_cookie', 'No cookie found')
    return HttpResponse(f'Cookie Value: {cookie_value}')