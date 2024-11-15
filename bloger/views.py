from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, auth
from django.contrib import messages
from .forms import BlogPostForm, CommentForm
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from .models import UserProfile
from django.utils import timezone
from datetime import timedelta
from .forms import CommentForm
import logging
from django.views.decorators.http import require_POST
from django.views import View

from django.views.generic import ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator


from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import IntegrityError, transaction
from django.db.models import Q, Count
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from datetime import timedelta
import logging

from .forms import BlogPostForm, CommentForm, UserProfileForm, CategoryForm
from .models import BlogPost, Comment, Category, UserProfile, PostView, ProfileLike, UserFollow

logger = logging.getLogger(__name__)

# Utility Functions
def generate_unique_slug(model_instance, title, slug_field_name="slug"):
    """Generate a unique slug for a model instance."""
    slug = slugify(title)
    unique_slug = slug
    model_class = model_instance.__class__
    
    # Query existing objects with similar slugs for efficiency
    existing_slugs = model_class.objects.filter(
        **{f"{slug_field_name}__startswith": slug}
    ).values_list(slug_field_name, flat=True)
    
    if unique_slug in existing_slugs:
        max_similar = model_class.objects.filter(
            **{f"{slug_field_name}__regex": f"^{slug}-[0-9]+$"}
        ).count()
        unique_slug = f"{slug}-{max_similar + 1}"
    
    return unique_slug

@login_required
def profile_view(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    return render(request, 'profile.html', {'profile': profile})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, DetailView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count

class ProfileDetailView(DetailView):
    model = UserProfile
    template_name = 'profile.html'
    context_object_name = 'profile'
    
    def get_object(self, queryset=None):
        return get_object_or_404(
            UserProfile.objects.select_related('user')
            .annotate(
                post_count=Count('user__blog_posts'),
            ),
            user__username=self.kwargs.get('username')
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.get_object()
        user = self.request.user
        
        if user.is_authenticated:
            context['is_following'] = profile.is_followed_by(user)
            context['is_liked'] = profile.is_liked_by(user)
            
        context['total_followers'] = profile.follower_count
        context['total_following'] = profile.following_count
        context['total_likes'] = profile.like_count
        context['post_count'] = profile.post_count
        context['is_own_profile'] = user == profile.user
        
        return context

class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'profile_edit.html'
    
    def get_object(self, queryset=None):
        return self.request.user.profile
    
    def get_success_url(self):
        return reverse('profile_detail', kwargs={'username': self.request.user.username})
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

@login_required
def toggle_follow(request, username):
    profile = get_object_or_404(UserProfile, user__username=username)
    user = request.user
    
    if profile.user != user:
        if profile.is_followed_by(user):
            UserFollow.objects.filter(
                follower=user,
                following=profile
            ).delete()
            is_following = False
        else:
            UserFollow.objects.create(
                follower=user,
                following=profile
            )
            is_following = True
            
        return JsonResponse({
            'is_following': is_following,
            'follower_count': profile.follower_count
        })
    
    return JsonResponse({'error': 'You cannot follow yourself'}, status=400)

@login_required
def toggle_like(request, username):
    profile = get_object_or_404(UserProfile, user__username=username)
    user = request.user
    
    if profile.user != user:
        if profile.is_liked_by(user):
            ProfileLike.objects.filter(
                user=user,
                profile=profile
            ).delete()
            is_liked = False
        else:
            ProfileLike.objects.create(
                user=user,
                profile=profile
            )
            is_liked = True
            
        return JsonResponse({
            'is_liked': is_liked,
            'like_count': profile.like_count
        })
    
    return JsonResponse({'error': 'You cannot like your own profile'}, status=400)


class FollowerListView(ListView):
    template_name = 'profiles/follower_list.html'
    context_object_name = 'followers'
    paginate_by = 20

    def get_queryset(self):
        self.profile = get_object_or_404(UserProfile, 
            user__username=self.kwargs['username']
        )
        return self.profile.followers.select_related('profile').order_by('-userfollow__created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
        return context

class FollowingListView(ListView):
    template_name = 'profiles/following_list.html'
    context_object_name = 'following'
    paginate_by = 20

    def get_queryset(self):
        self.profile = get_object_or_404(UserProfile, 
            user__username=self.kwargs['username']
        )
        return self.profile.user.following.select_related('profile').order_by('-userfollow__created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
        return context



@login_required
def load_followers(request, username):
    profile = get_object_or_404(UserProfile, user__username=username)
    page = request.GET.get('page', 1)
    
    followers = profile.followers.select_related('profile').order_by(
        '-userfollow__created_at'
    )
    
    paginator = Paginator(followers, 20)
    followers_page = paginator.get_page(page)
    
    html = render_to_string(
        'profiles/includes/follower_list_items.html',
        {'followers': followers_page},
        request=request
    )
    
    return JsonResponse({
        'html': html,
        'has_next': followers_page.has_next(),
        'next_page': followers_page.next_page_number() if followers_page.has_next() else None
    })

@login_required
def load_following(request, username):
    profile = get_object_or_404(UserProfile, user__username=username)
    page = request.GET.get('page', 1)
    
    following = profile.user.following.select_related('profile').order_by(
        '-userfollow__created_at'
    )
    
    paginator = Paginator(following, 20)
    following_page = paginator.get_page(page)
    
    html = render_to_string(
        'profiles/includes/following_list_items.html',
        {'following': following_page},
        request=request
    )
    
    return JsonResponse({
        'html': html,
        'has_next': following_page.has_next(),
        'next_page': following_page.next_page_number() if following_page.has_next() else None
    })





# Class-based Views
class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'profile_edit.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user.profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)
        



from django.views.generic import ListView
from django.db.models import Count, Q
from django.utils import timezone
from .models import BlogPost, PostView

class BlogListView(ListView):
    model = BlogPost
    template_name = 'index.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        """
        Get the list of blog posts with optimized queries and search functionality.
        """
        # Base queryset with optimized joins
        queryset = BlogPost.objects.select_related(
            'writer', 
            'category'
        ).prefetch_related(
            'likes'
        ).filter(
            status='published'
        ).order_by('-created_on')

        # Handle search functionality
        query = self.request.GET.get('query')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(body__icontains=query) |
                Q(writer__username__icontains=query)
            )

        return queryset

    def total_likes(self, post):
        """
        Return the total likes for a post.
        """
        return post.likes.count()

    def total_comments(self, post):
        """
        Return the total comments for a post.
        """
        return post.comments.count()

    def increment_view_count(self, post, user):
        """
        Increment view count for unique users.
        """
        if user.is_authenticated:
            # Only count a view if it doesn't already exist for this user and post
            PostView.objects.get_or_create(
                post=post,
                user=user,
                defaults={'timestamp': timezone.now()}
            )

    def get_context_data(self, **kwargs):
        """
        Add additional context data including featured posts, recent posts, and popular posts.
        """
        context = super().get_context_data(**kwargs)
        
        # Featured posts
        context['featured_posts'] = BlogPost.objects.select_related(
            'writer', 
            'category'
        ).filter(
            status='published',
            featured=True
        ).order_by(
            '-created_on'
        )[:5]

        # Recent posts
        context['recent_posts'] = BlogPost.objects.select_related(
            'writer', 
            'category'
        ).filter(
            status='published'
        ).order_by(
            '-created_on'
        )[:4]

        # Popular posts based on like count
        context['popular_posts'] = BlogPost.objects.select_related(
            'writer', 
            'category'
        ).filter(
            status='published'
        ).annotate(
            like_count=Count('likes')
        ).order_by(
            '-like_count',
            '-created_on'  # Secondary ordering for posts with same like count
        )[:5]

        # Add search query to context if it exists
        if 'query' in self.request.GET:
            context['search_query'] = self.request.GET['query']

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
    
    # Featured posts
            context['featured_posts'] = BlogPost.objects.filter(status='published', featured=True).order_by('-created_on')[:5]

    # Recent posts
            context['recent_posts'] = BlogPost.objects.filter(status='published').order_by('-created_on')[:4]

    # Popular posts, ordered by likes
            context['popular_posts'] = BlogPost.objects.filter(status='published').annotate(
                like_count=Count('likes')
            ).order_by('-like_count', '-created_on')[:5]

        return context

# Function-based Views
@cache_page(60 * 15)  # Cache for 15 minutes
def about(request):
    return render(request, 'about.html')

@login_required
@require_http_methods(["GET", "POST"])
def create_blog_post(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    post = form.save(commit=False)
                    post.writer = request.user
                    post.slug = generate_unique_slug(post, post.title)
                    post.save()
                    form.save_m2m()
                    
                messages.success(request, 'Blog post created successfully.')
                logger.info(f"Blog post '{post.title}' created by {request.user}")
                return redirect('post_detail', slug=post.slug)
                
            except IntegrityError as e:
                logger.error(f"Failed to create blog post: {str(e)}")
                messages.error(request, 'An error occurred while creating the post.')
                
    else:
        form = BlogPostForm()
    
    return render(request, 'create_blog_post.html', {'form': form})

@login_required
@require_http_methods(["GET", "POST"])
def edit_blog_post(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    
    if post.writer != request.user and not request.user.is_staff:
        raise PermissionDenied
        
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            try:
                with transaction.atomic():
                    post = form.save()
                messages.success(request, 'Blog post updated successfully.')
                logger.info(f"Blog post '{post.title}' updated by {request.user}")
                return redirect('blog_detail', slug=post.slug)
            except IntegrityError as e:
                logger.error(f"Failed to update blog post: {str(e)}")
                messages.error(request, 'An error occurred while updating the post.')
    else:
        form = BlogPostForm(instance=post)
    
    return render(request, 'edit_blog_post.html', {'form': form, 'post': post})

logger = logging.getLogger(__name__)
@login_required
def delete_blog_post(request, slug):
    blog_post = get_object_or_404(BlogPost, slug=slug)
    if blog_post.writer != request.user:
        messages.error(request, "You are not authorized to delete this post.")
        logger.warning(f"Unauthorized delete attempt by user {request.user} on post {slug}")
        return redirect('blog_detail', slug=slug)

    if request.method == 'POST':
        blog_post.delete()
        messages.success(request, "Blog post deleted successfully.")
        return redirect('index')

    return render(request, 'delete_blog_post.html', {'blog_post': blog_post})

@method_decorator(login_required, name='dispatch')
class DraftPostListView(View):
    template_name = 'draft_posts.html'

    def get(self, request):
        # Filter posts with status 'draft' created by the current user
        drafts = BlogPost.objects.filter(status='draft', writer=request.user).order_by('-created_on')
        context = {
            'drafts': drafts
        }
        return render(request, self.template_name, context)

@login_required
@require_POST
def like_post(request):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        raise Http404
        
    post_id = request.POST.get('post_id')
    if not post_id:
        return JsonResponse({'error': 'Post ID required'}, status=400)
        
    try:
        post = BlogPost.objects.get(id=post_id)
        user = request.user
        
        if post.likes.filter(id=user.id).exists():
            post.likes.remove(user)
            liked = False
        else:
            post.likes.add(user)
            liked = True
            
        return JsonResponse({
            'liked': liked,
            'total_likes': post.total_likes(),
            'post_id': post_id
        })
    except BlogPost.DoesNotExist:
        return JsonResponse({'error': 'Post not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in like_post: {str(e)}")
        return JsonResponse({'error': 'Server error'}, status=500)

@login_required
@require_http_methods(["POST"])  # Only allow POST requests for comments
def comment_post(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.commenter = request.user
            
            # Handle nested comments
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent = Comment.objects.get(id=parent_id, post=post)
                    comment.parent = parent
                except Comment.DoesNotExist:
                    messages.error(request, 'Parent comment not found.')
                    return redirect('blog_detail', slug=slug)
            
            comment.save()
            messages.success(request, 'Comment added successfully.')
        else:
            messages.error(request, 'Please correct the errors below.')
            
    return redirect('blog_detail', slug=slug)

@require_http_methods(["GET"])
def post_detail_view(request, slug):
    post = get_object_or_404(
        BlogPost.objects.select_related(
            'writer', 
            'category'
        ).prefetch_related(
            'comments__commenter',
            'comments__replies__commenter'
        ), 
        slug=slug
    )
    
    # Increment view count for authenticated users
    if request.user.is_authenticated:
        post.increment_view_count(request.user)
    
    # Get recent posts (excluding current)
    recent_posts = BlogPost.objects.filter(
        status='published',
        created_on__gte=timezone.now() - timedelta(days=10)
    ).exclude(id=post.id)[:3]
    
    # Get related posts from same category
    related_posts = BlogPost.objects.filter(
        category=post.category,
        status='published'
    ).exclude(id=post.id)[:3]
    
    # Get root comments only (no replies)
    comments = post.comments.filter(parent__isnull=True).order_by('-created_on')
    
     # Get popular posts based on likes and views
    popular_posts = BlogPost.objects.annotate(
            like_count=Count('likes'),
            view_count=Count('views')
        ).filter(
            status='published'
        ).exclude(
            id=post.id
        ).order_by(
            '-like_count',
            '-view_count',
            '-created_on'
        )[:5]
        
        # Get root comments only (no replies)
    comments = post.comments.filter(
            parent__isnull=True
        ).select_related(
            'commenter'
        ).prefetch_related(
            'replies__commenter'
        ).order_by('-created_on')
    context = {
            'post': post,
            'comments': comments,
            'comment_form': CommentForm(),
            'recent_posts': recent_posts,
            'related_posts': related_posts,
            'popular_posts': popular_posts,
            'is_liked': post.likes.filter(id=request.user.id).exists() if request.user.is_authenticated else False,
            'total_likes': post.likes.count(),
            'total_comments': post.comments.count(),
        }
    return render(request, 'blog_detail.html', context)

@require_http_methods(["GET"])
def category_detail_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    
    posts_list = category.posts.filter(status='published').order_by('-created_on')
    paginator = Paginator(posts_list, 10)
    
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    
    context = {
        'category': category,
        'posts': posts,
        'total_posts': posts_list.count(),
    }
    
    return render(request, 'category.html', context)

# Authentication Views
@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')
            
        try:
            with transaction.atomic():
                if User.objects.filter(username=username).exists():
                    messages.error(request, 'Username is already taken.')
                    return redirect('register')
                    
                if User.objects.filter(email=email).exists():
                    messages.error(request, 'Email is already registered.')
                    return redirect('register')
                    
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                messages.success(request, 'Account created successfully. Please log in.')
                return redirect('login')
                
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            messages.error(request, 'An error occurred during registration.')
            
    return render(request, 'register.html')

@require_http_methods(["GET", "POST"])
def login(request):
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
            
    return render(request, 'login.html')

@login_required
def logout(request):
    auth.logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('index')

# Search, Index, and Detailed Views
def search_results(request):
    query = request.GET.get('query')
    results = BlogPost.objects.filter(title__icontains=query)
    return render(request, 'search_results.html', {'query': query, 'results': results})





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



