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
from django.contrib.auth.mixins import LoginRequiredMixin
from django_ckeditor_5.views import upload_file

from django.views.generic import ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.db.models import Sum, F


from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
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

from shop.models import Product, Order, Category
from shop.forms import ProductForm, OrderCreateForm, ProductSearchForm

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
    
    # Calculate shop statistics
    total_revenue = Order.objects.filter(
        product__seller=request.user
    ).aggregate(
        total=Sum(F('quantity') * F('unit_price'))
    )['total'] or 0
    
    active_listings = Product.objects.filter(
        seller=request.user,
        status='active'
    ).count()
    
    context = {
        'profile': profile,
        'total_revenue': total_revenue,
        'active_listings': active_listings,
    }
    return render(request, 'profile.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, DetailView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count

from django.db.models import Count, Q

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User



class ProfileDetailView(DetailView):
    model = UserProfile
    template_name = 'profile.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        username = self.kwargs.get('username')
        user = get_object_or_404(User, username=username)
        
        # Get or create the user profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # If we're using annotated fields, we need to refetch with annotations
        if not queryset:
            queryset = UserProfile.objects.select_related('user').annotate(
                post_count_annotated=Count('user__blog_posts', filter=Q(user__blog_posts__status='published')),
                like_count_annotated=Count('likes'),
                follower_count_annotated=Count('followers')
            )
        
        return get_object_or_404(queryset, user=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.get_object()
        user = self.request.user

        # Check if authenticated user is following or liking the profile
        if user.is_authenticated:
            context['is_following'] = profile.is_followed_by(user)
            context['is_liked'] = profile.is_liked_by(user)

        # Use the annotated counts in context, not the properties
        context['total_followers'] = getattr(profile, 'follower_count_annotated', profile.follower_count)
        context['total_following'] = profile.following_count
        context['total_likes'] = getattr(profile, 'like_count_annotated', profile.like_count)
        context['post_count'] = getattr(profile, 'post_count_annotated', 
            BlogPost.objects.filter(writer=profile.user, status='published').count())

        # Get posts for the profile's user (published only)
        context['posts'] = BlogPost.objects.filter(writer=profile.user, status='published').order_by('-created_on')

        # Check if the user is viewing their own profile
        context['is_own_profile'] = user == profile.user

        return context

class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'profile_edit.html'
    
    def get_object(self, queryset=None):
        """Get the user's profile, creating one if it doesn't exist"""
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_form_kwargs(self):
        """Pass additional information to the form"""
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_object()
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Add additional context for the template"""
        context = super().get_context_data(**kwargs)
        # Add information about whether user is a seller
        context['is_seller'] = self.request.user.products.exists()
        # Add user to context for the template
        context['user'] = self.request.user
        return context
    
    def form_valid(self, form):
        """Process the valid form"""
        # Set specific message based on actions taken
        messages.success(self.request, 'Your profile has been updated successfully.')
        
        # Check if WhatsApp notifications are enabled but no number provided
        if form.cleaned_data.get('receive_order_whatsapp') and not form.cleaned_data.get('whatsapp_phone'):
            # If regular phone is available, use it for WhatsApp
            if form.cleaned_data.get('phone'):
                form.instance.whatsapp_phone = form.cleaned_data.get('phone')
                messages.info(self.request, 'Your regular phone number will be used for WhatsApp notifications.')
        
        return super().form_valid(form)
    
    def get_success_url(self):
        """Return to profile page after successful update"""
        return reverse('profile_detail', kwargs={'username': self.request.user.username})

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
            
        # Add shop-related data
        from shop.models import Product, Category
        
        # Featured products for shop section
        context['featured_products'] = Product.objects.filter(
            status='active',
            featured=True
        ).select_related('category').order_by('-created_on')[:6]
        
        # Shop categories
        context['shop_categories'] = Category.objects.all()

        return context


    
#BLOGPOST LIKE
@login_required
@require_POST
def like_post(request):
    post_id = request.POST.get('post_id')
    if not post_id:
        return JsonResponse({'error': 'Post ID required'}, status=400)

    try:
        post = BlogPost.objects.get(id=post_id)
        user = request.user

        # Toggle the like status directly
        if user in post.likes.all():
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
    
# Function-based Views
@cache_page(60 * 15)  # Cache for 15 minutes
def about(request):
    return render(request, 'about.html')



import json
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from .models import BlogPost
from .forms import BlogPostForm

logger = logging.getLogger(__name__)

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
@require_http_methods(["GET", "POST"])
def create_blog_post(request):
    """
    Create a new blog post with support for video embeds.
    Handles both GET (display form) and POST (process form) requests.
    """
    context = {
        'page_title': 'Create New Blog Post',
        'submit_text': 'Create Post',
        'is_new_post': True
    }
    
    # Handle a potential "remove_image" hidden field
    remove_image = request.POST.get('remove_image') == 'true'
    
    # Get video embeds from hidden field if present
    video_embeds = []
    video_embeds_json = request.POST.get('video_embeds', '[]')
    if video_embeds_json:
        try:
            video_embeds = json.loads(video_embeds_json)
            logger.debug(f"Found {len(video_embeds)} video embeds")
        except json.JSONDecodeError:
            logger.warning("Failed to parse video_embeds JSON")
    
    if request.method == 'POST':
        form = BlogPostForm(
            request.POST, 
            request.FILES,
            initial={'writer': request.user}
        )
        
        # Debug information
        logger.debug(f"Form data: {request.POST}")
        
        # Check if the form is valid
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create post but don't save to DB yet
                    post = form.save(commit=False)
                    post.writer = request.user
                    
                    # Generate unique slug
                    post.slug = generate_unique_slug(post, post.title)
                    
                    # Process video embeds if they exist
                    if video_embeds:
                        logger.debug("Adding video embeds to post content")
                        # Add video embeds to the content
                        body_content = post.body or ""
                        
                        # Only add embeds if they're not already in the content
                        for embed in video_embeds:
                            if embed not in body_content:
                                if body_content:
                                    body_content += f"\n\n{embed}\n\n"
                                else:
                                    body_content = f"{embed}\n\n"
                        
                        post.body = body_content
                    
                    # Set published date if status is published
                    if post.status == 'published':
                        post.published_on = timezone.now()
                    
                    # Save the post
                    post.save()
                    
                    # Save many-to-many relationships
                    form.save_m2m()
                    
                    # Success message
                    messages.success(
                        request, 
                        'Your blog post has been created successfully!'
                    )
                    
                    # Log success
                    logger.info(
                        f"Blog post '{post.title}' (ID: {post.id}) "
                        f"created by user {request.user.username} "
                        f"(ID: {request.user.id})"
                    )
                    
                    # Redirect to the post detail page
                    return redirect('post_detail', slug=post.slug)
            
            except IntegrityError as e:
                logger.error(
                    f"Database error while creating blog post: {str(e)}, "
                    f"User: {request.user.username}"
                )
                messages.error(
                    request,
                    'A database error occurred while saving your post. Please try again.'
                )
            
            except ValidationError as e:
                logger.error(
                    f"Validation error while creating blog post: {str(e)}, "
                    f"User: {request.user.username}"
                )
                messages.error(
                    request,
                    f'Validation error: {str(e)}'
                )
                
            except Exception as e:
                logger.error(
                    f"Unexpected error while creating blog post: {str(e)}, "
                    f"User: {request.user.username}"
                )
                messages.error(
                    request,
                    'An unexpected error occurred. Please try again later.'
                )
        else:
            # Log form errors
            logger.warning(
                f"Invalid form submission for new blog post by "
                f"user {request.user.username}. Errors: {form.errors}"
            )
            
            # Add form errors to messages for better visibility
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f"Error: {error}")
                    else:
                        messages.error(request, f"Error in {field}: {error}")
    else:
        # GET request - create a new form
        form = BlogPostForm()
    
    # Add form to context
    context['form'] = form
    
    # Render the template with the form
    return render(request, 'create_blog_post.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def edit_blog_post(request, slug):
    """
    Edit an existing blog post.
    Handles both GET (display form) and POST (process form) requests.
    """
    try:
        post = get_object_or_404(BlogPost, slug=slug)
        
        # Check permissions
        if post.writer != request.user and not request.user.is_staff:
            logger.warning(
                f"Unauthorized edit attempt on post '{post.title}' by "
                f"user {request.user.username}"
            )
            raise PermissionDenied(
                "You don't have permission to edit this post."
            )
        
        if request.method == 'POST':
            form = BlogPostForm(
                request.POST,
                request.FILES,
                instance=post
            )
            
            if form.is_valid():
                try:
                    with transaction.atomic():
                        post = form.save(commit=False)
                        
                        # Handle status changes
                        if post.status == 'published' and not post.published_on:
                            post.published_on = timezone.now()
                            
                        post.save()
                        form.save_m2m()
                        
                        messages.success(
                            request,
                            'Your blog post has been updated successfully!'
                        )
                        logger.info(
                            f"Blog post '{post.title}' (ID: {post.id}) "
                            f"updated by user {request.user.username}"
                        )
                        return redirect('post_detail', slug=post.slug)
                        
                except IntegrityError as e:
                    logger.error(
                        f"Database error while updating blog post: {str(e)}, "
                        f"Post: {post.title}, User: {request.user.username}"
                    )
                    messages.error(
                        request,
                        'An error occurred while saving your changes. Please try again.'
                    )
                    
                except Exception as e:
                    logger.error(
                        f"Unexpected error while updating blog post: {str(e)}, "
                        f"Post: {post.title}, User: {request.user.username}"
                    )
                    messages.error(
                        request,
                        'An unexpected error occurred. Please try again later.'
                    )
            
            else:
                logger.warning(
                    f"Invalid form submission for editing blog post '{post.title}' "
                    f"by user {request.user.username}. Errors: {form.errors}"
                )
        else:
            form = BlogPostForm(instance=post)
            
        return render(request, 'edit_blog_post.html', {
            'form': form,
            'post': post,
            'page_title': f'Edit: {post.title}',
            'submit_text': 'Update Post',
            'is_new_post': False
        })
        
    except PermissionDenied as e:
        raise
        
    except Exception as e:
        logger.error(
            f"Critical error in edit_blog_post view: {str(e)}, "
            f"Slug: {slug}, User: {request.user.username}"
        )
        messages.error(
            request,
            'A critical error occurred. Please contact support if this persists.'
        )
        return redirect('index')

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

def toggle_like(self, user):
    """Add or remove a like for the post from a user."""
    if user in self.likes.all():
        self.likes.remove(user)
        liked = False
    else:
        self.likes.add(user)
        liked = True
    self.save()
    return liked


@login_required
@require_POST
def like_post(request):
    post_id = request.POST.get('post_id')
    if not post_id:
        return JsonResponse({'error': 'Post ID required'}, status=400)

    try:
        post = BlogPost.objects.get(id=post_id)
        user = request.user

        # Toggle the like status
        liked = post.toggle_like(user)
        
        return JsonResponse({
            'liked': liked,
            'total_likes': post.total_likes(),  # Use the total_likes method to get the updated count
            'post_id': post_id
        })
    except BlogPost.DoesNotExist:
        return JsonResponse({'error': 'Post not found'}, status=404)

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

@login_required(login_url='/login/')
@require_http_methods(["POST"])
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


def post_detail_view(request, slug):
    """
    Display a blog post with enhanced video embed processing.
    """
    post = get_object_or_404(
        BlogPost.objects.select_related(
            'writer', 
            'writer__profile',
            'category'
        ).prefetch_related(
            'comments__commenter',
            'comments__commenter__profile',
            'comments__replies__commenter',
            'comments__replies__commenter__profile'
        ), 
        slug=slug
    )
    
    # Process video embeds in the content if necessary
    if '<iframe' in post.body and not '<div class="video-container">' in post.body:
        from django.utils.safestring import mark_safe
        import re
        
        # Enhanced pattern to catch more variations of video embeds
        pattern = r'(<iframe[^>]*src=["\'](https?:\/\/)?(www\.)?(youtube\.com|youtu\.be|vimeo\.com|player\.vimeo\.com)[^>]*<\/iframe>)'
        replacement = r'<div class="video-container">\1</div>'
        post.body = mark_safe(re.sub(pattern, replacement, post.body))
    
    # Handle direct video URLs that might be in the content
    if ('youtube.com/watch?v=' in post.body or 'youtu.be/' in post.body) and not '<iframe' in post.body:
        from django.utils.safestring import mark_safe
        import re
        
        # Convert direct YouTube URLs to embedded iframes
        youtube_pattern = r'(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})'
        
        def youtube_replacement(match):
            video_id = match.group(4)
            return f'<div class="video-container"><iframe src="https://www.youtube.com/embed/{video_id}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>'
        
        post.body = mark_safe(re.sub(youtube_pattern, youtube_replacement, post.body))
    
    # Increment view count for authenticated users
    if request.user.is_authenticated:
        post.increment_view_count(request.user)
    
    # Get recent posts (excluding current)
    recent_posts = BlogPost.objects.filter(
        status='published',
        created_on__gte=timezone.now() - timedelta(days=30)
    ).exclude(id=post.id)[:3]
    
    # Get related posts from same category
    related_posts = BlogPost.objects.filter(
        category=post.category,
        status='published'
    ).exclude(id=post.id)[:4]
    
    # Get popular posts based on likes and views
    popular_posts = BlogPost.objects.annotate(
        like_count=Count('likes'),
        view_count=F('views')
    ).filter(
        status='published'
    ).exclude(
        id=post.id
    ).order_by(
        '-like_count',
        '-view_count',
        '-created_on'
    )[:5]
    
    # Get categories for sidebar
    categories = Category.objects.all()
    
    # Get root comments only (no replies)
    comments = post.comments.filter(
        parent__isnull=True
    ).select_related(
        'commenter',
        'commenter__profile'
    ).prefetch_related(
        'replies__commenter',
        'replies__commenter__profile'
    ).order_by('-created_on')
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': CommentForm(),
        'recent_posts': recent_posts,
        'related_posts': related_posts,
        'popular_posts': popular_posts,
        'categories': categories,
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
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken.')
            return redirect('register')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered.')
            return redirect('register')
        
        try:
            # First just create the user without a transaction
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Then try to create the profile if needed
            try:
                if not UserProfile.objects.filter(user=user).exists():
                    UserProfile.objects.create(
                        user=user,
                        bio="",  # Empty default bio
                    )
            except Exception as profile_error:
                logger.error(f"Profile creation error: {str(profile_error)}")
                # Don't fail the registration if profile creation fails
                # We'll handle creating the profile later
            
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
            logger.warning(f"Failed login attempt for username: {username}")
    
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

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create a UserProfile when a new User is created.
    """
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal to save the UserProfile when the User is saved.
    """
    # Create profile if it doesn't exist yet
    if not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()




