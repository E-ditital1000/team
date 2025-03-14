from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum, F
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from datetime import timedelta
import csv
import json

from .models import (
    BlogPost, Comment, UserProfile, Category, 
    PostView, ProfileLike, UserFollow
)

# Custom filters
class PublicationStatusFilter(SimpleListFilter):
    title = _('Publication Status')
    parameter_name = 'pub_status'

    def lookups(self, request, model_admin):
        return (
            ('published', _('Published')),
            ('draft', _('Draft')),
            ('recent', _('Published in last week')),
            ('month', _('Published this month')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'published':
            return queryset.filter(status='published')
        if self.value() == 'draft':
            return queryset.filter(status='draft')
        if self.value() == 'recent':
            last_week = timezone.now() - timedelta(days=7)
            return queryset.filter(status='published', published_on__gte=last_week)
        if self.value() == 'month':
            last_month = timezone.now() - timedelta(days=30)
            return queryset.filter(status='published', published_on__gte=last_month)


class PopularPostFilter(SimpleListFilter):
    title = _('Popularity')
    parameter_name = 'popularity'

    def lookups(self, request, model_admin):
        return (
            ('high_views', _('High Views (>100)')),
            ('high_likes', _('High Likes (>10)')),
            ('high_comments', _('High Comments (>5)')),
            ('trending', _('Trending (views+likes+comments)')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'high_views':
            return queryset.filter(views__gt=100)
        if self.value() == 'high_likes':
            return queryset.annotate(like_count=Count('likes')).filter(like_count__gt=10)
        if self.value() == 'high_comments':
            return queryset.annotate(comment_count=Count('comments')).filter(comment_count__gt=5)
        if self.value() == 'trending':
            return queryset.annotate(
                like_count=Count('likes'),
                comment_count=Count('comments')
            ).filter(
                (F('views') + F('like_count') + F('comment_count')) > 20
            )


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'status_badge', 'writer_link', 'category_link', 
        'created_on', 'views', 'total_likes', 'comment_count', 
        'featured', 'preview_link'
    )
    list_filter = (
        PublicationStatusFilter, 
        PopularPostFilter,
        'featured', 
        'category', 
        'writer'
    )
    search_fields = ('title', 'subtitle', 'body', 'writer__username', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('writer',)
    date_hierarchy = 'created_on'
    list_per_page = 25
    actions = ['make_published', 'make_draft', 'toggle_featured', 'export_as_csv']
    list_editable = ('featured',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'subtitle', 'slug', 'writer')
        }),
        (_('Content'), {
            'fields': ('body', 'image', 'category', 'tags')
        }),
        (_('Status'), {
            'fields': ('status', 'featured', 'created_on', 'published_on'),
            'classes': ('collapse',)
        }),
        (_('Metrics'), {
            'fields': ('views',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_on', 'published_on', 'views')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'blog_stats/',
                self.admin_site.admin_view(self.blog_stats_view),
                name='blog_stats',
            ),
        ]
        return custom_urls + urls

    def blog_stats_view(self, request):
        # Get stats data
        total_posts = BlogPost.objects.count()
        published_posts = BlogPost.objects.filter(status='published').count()
        draft_posts = BlogPost.objects.filter(status='draft').count()
        total_views = BlogPost.objects.aggregate(Sum('views'))['views__sum'] or 0
        total_comments = Comment.objects.count()
        
        # Top posts
        most_viewed = BlogPost.objects.order_by('-views')[:5]
        most_liked = BlogPost.objects.annotate(
            like_count=Count('likes')
        ).order_by('-like_count')[:5]
        most_commented = BlogPost.objects.annotate(
            comment_count=Count('comments')
        ).order_by('-comment_count')[:5]
        
        # Writers stats
        top_writers = User.objects.annotate(
            post_count=Count('blog_posts')
        ).order_by('-post_count')[:5]
        
        context = {
            'title': _('Blog Statistics'),
            'total_posts': total_posts,
            'published_posts': published_posts,
            'draft_posts': draft_posts,
            'total_views': total_views,
            'total_comments': total_comments,
            'most_viewed': most_viewed,
            'most_liked': most_liked,
            'most_commented': most_commented,
            'top_writers': top_writers,
            'opts': self.model._meta,
        }
        
        return TemplateResponse(request, 'admin/blog_stats.html', context)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _comment_count=Count('comments', distinct=True),
            _like_count=Count('likes', distinct=True),
        )
        return queryset

    def status_badge(self, obj):
        colors = {
            'draft': 'secondary',
            'published': 'success'
        }
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            colors[obj.status],
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')

    def writer_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.writer.id])
        return format_html('<a href="{}">{}</a>', url, obj.writer.username)
    writer_link.short_description = _('Writer')
    
    def category_link(self, obj):
        if obj.category:
            url = reverse('admin:bloger_category_change', args=[obj.category.id])
            return format_html('<a href="{}">{}</a>', url, obj.category.name)
        return "-"
    category_link.short_description = _('Category')

    def comment_count(self, obj):
        return obj._comment_count
    comment_count.short_description = _('Comments')
    comment_count.admin_order_field = '_comment_count'

    def total_likes(self, obj):
        return obj._like_count
    total_likes.short_description = _('Likes')
    total_likes.admin_order_field = '_like_count'
    
    def preview_link(self, obj):
        if obj.status == 'published':
            url = obj.get_absolute_url()
            return format_html('<a href="{}" target="_blank">👁️ View</a>', url)
        return ""
    preview_link.short_description = _('Preview')

    # Admin actions
    def make_published(self, request, queryset):
        updated = queryset.filter(status='draft').update(
            status='published', 
            published_on=timezone.now()
        )
        self.message_user(request, _(
            f'{updated} posts were successfully marked as published.'
        ))
    make_published.short_description = _("Mark selected posts as published")

    def make_draft(self, request, queryset):
        updated = queryset.filter(status='published').update(status='draft')
        self.message_user(request, _(
            f'{updated} posts were successfully marked as draft.'
        ))
    make_draft.short_description = _("Mark selected posts as draft")
    
    def toggle_featured(self, request, queryset):
        for post in queryset:
            post.featured = not post.featured
            post.save()
        self.message_user(request, _('Featured status toggled successfully.'))
    toggle_featured.short_description = _("Toggle featured status")
    
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields if field.name not in ('body',)]
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta}.csv'
        writer = csv.writer(response)
        
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
            
        return response
    export_as_csv.short_description = _("Export selected posts as CSV")
    
    class Media:
        css = {
            'all': ('admin/css/blog_admin.css',)
        }
        js = ('admin/js/blog_admin.js',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'truncated_comment', 'post_link', 'commenter_link', 
        'created_on', 'is_approved', 'is_reply', 'parent_comment'
    )
    list_filter = ('created_on', 'is_approved', 'commenter')
    search_fields = ('body', 'commenter__username', 'post__title')
    raw_id_fields = ('post', 'commenter', 'parent')
    list_editable = ('is_approved',)
    date_hierarchy = 'created_on'
    list_per_page = 50
    actions = ['approve_comments', 'unapprove_comments']

    def truncated_comment(self, obj):
        return obj.body[:100] + '...' if len(obj.body) > 100 else obj.body
    truncated_comment.short_description = _('Comment')

    def post_link(self, obj):
        url = reverse('admin:bloger_blogpost_change', args=[obj.post.id])
        return format_html('<a href="{}">{}</a>', url, obj.post.title)
    post_link.short_description = _('Post')

    def commenter_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.commenter.id])
        return format_html('<a href="{}">{}</a>', url, obj.commenter.username)
    commenter_link.short_description = _('Commenter')

    def parent_comment(self, obj):
        if obj.parent:
            url = reverse('admin:bloger_comment_change', args=[obj.parent.id])
            return format_html('<a href="{}">View Parent</a>', url)
        return "-"
    parent_comment.short_description = _('Parent')

    def is_reply(self, obj):
        return bool(obj.parent)
    is_reply.boolean = True
    is_reply.short_description = _('Is Reply')
    
    # Admin actions
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, _(
            f'{updated} comments were successfully approved.'
        ))
    approve_comments.short_description = _("Approve selected comments")
    
    def unapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, _(
            f'{updated} comments were successfully unapproved.'
        ))
    unapprove_comments.short_description = _("Unapprove selected comments")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user_link', 
        'phone_display',
        'business_name',
        'career', 
        'location',
        'profile_picture_preview',
        'follower_count', 
        'following_count', 
        'like_count', 
        'last_active'
    )
    
    search_fields = (
        'user__username', 
        'user__email', 
        'bio', 
        'career',
        'business_name',
        'phone',
        'whatsapp_phone', 
        'nationality',
        'location'
    )
    
    list_filter = (
        'receive_order_emails',
        'receive_order_whatsapp',
        'career', 
        'nationality',
        'location', 
        'last_active'
    )
    
    raw_id_fields = ('user',)
    
    actions = ['export_profiles_csv', 'toggle_email_notifications', 'toggle_whatsapp_notifications']

    fieldsets = (
        (None, {
            'fields': (
                'user', 
                'bio',
                'profile_picture',
                'cover_photo'
            )
        }),
        (_('Contact Information'), {
            'fields': (
                'phone',
                'whatsapp_phone',
                'location',
                'linkedin',
                'website'
            )
        }),
        (_('Business Information'), {
            'fields': (
                'business_name',
                'business_address'
            ),
            'classes': ('collapse',)
        }),
        (_('Personal Information'), {
            'fields': (
                'career', 
                'nationality', 
                'birthday'
            ),
            'classes': ('collapse',)
        }),
        (_('Professional Details'), {
            'fields': (
                'education', 
                'skills', 
                'projects', 
                'recommendations',
                'work_experience'
            ),
            'classes': ('collapse',)
        }),
        (_('Notification Settings'), {
            'fields': (
                'receive_order_emails',
                'receive_order_whatsapp'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('last_active',)

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = _('User')
    
    def phone_display(self, obj):
        phone = obj.phone or "-"
        whatsapp = obj.whatsapp_phone or "-"
        if obj.phone == obj.whatsapp_phone and obj.phone:
            return format_html("📞 {} (Same for WhatsApp)", phone)
        return format_html("📞 {} / 📱 {}", phone, whatsapp)
    phone_display.short_description = _('Contact')

    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="max-height: 50px; border-radius: 25px;"/>',
                obj.profile_picture.url
            )
        return _("No Image")
    profile_picture_preview.short_description = _('Profile Picture')

    # Add JSON field formatting for better readability
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        json_fields = ['education', 'skills', 'projects', 'recommendations', 'work_experience']
        
        for field in json_fields:
            if field in form.base_fields:
                form.base_fields[field].widget.attrs.update({
                    'style': 'width: 90%; height: 100px; font-family: monospace;',
                    'class': 'json-prettify'
                })
                
                # If the object exists, format the JSON for better readability
                if obj and getattr(obj, field):
                    try:
                        value = getattr(obj, field)
                        if isinstance(value, str):
                            value = json.loads(value)
                        form.base_fields[field].initial = json.dumps(value, indent=2)
                    except (json.JSONDecodeError, TypeError):
                        pass  # Keep the original value if it can't be parsed
                        
        return form
    
    # Admin actions
    def export_profiles_csv(self, request, queryset):
        meta = self.model._meta
        # Exclude large fields and JSON fields
        exclude_fields = ['bio', 'education', 'skills', 'projects', 
                         'recommendations', 'work_experience']
        field_names = [field.name for field in meta.fields 
                     if field.name not in exclude_fields]
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=user_profiles.csv'
        writer = csv.writer(response)
        
        writer.writerow(['username', 'email'] + field_names)
        for obj in queryset:
            row = [obj.user.username, obj.user.email]
            for field in field_names:
                value = getattr(obj, field)
                if field in ['profile_picture', 'cover_photo']:
                    value = value.url if value else ''
                row.append(value)
            writer.writerow(row)
            
        return response
    export_profiles_csv.short_description = _("Export selected profiles as CSV")
    
    def toggle_email_notifications(self, request, queryset):
        for profile in queryset:
            profile.receive_order_emails = not profile.receive_order_emails
            profile.save()
        self.message_user(request, _('Email notification settings toggled.'))
    toggle_email_notifications.short_description = _("Toggle email notifications")
    
    def toggle_whatsapp_notifications(self, request, queryset):
        for profile in queryset:
            profile.receive_order_whatsapp = not profile.receive_order_whatsapp
            profile.save()
        self.message_user(request, _('WhatsApp notification settings toggled.'))
    toggle_whatsapp_notifications.short_description = _("Toggle WhatsApp notifications")

    class Media:
        css = {
            'all': ('admin/css/json_prettify.css',)
        }
        js = ('admin/js/json_prettify.js',)


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ('follower_link', 'following_link', 'created_at')
    list_filter = ('created_at',)
    search_fields = (
        'follower__username', 
        'follower__email',
        'following__user__username',
        'following__user__email'
    )
    raw_id_fields = ('follower', 'following')
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'follower',
            'following__user'
        )
        
    def follower_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.follower.id])
        return format_html('<a href="{}">{}</a>', url, obj.follower.username)
    follower_link.short_description = _('Follower')
    
    def following_link(self, obj):
        url = reverse('admin:bloger_userprofile_change', args=[obj.following.id])
        return format_html('<a href="{}">{}</a>', url, obj.following.user.username)
    following_link.short_description = _('Following')


@admin.register(ProfileLike)
class ProfileLikeAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'profile_link', 'created_at')
    list_filter = ('created_at',)
    search_fields = (
        'user__username',
        'user__email',
        'profile__user__username',
        'profile__user__email'
    )
    raw_id_fields = ('user', 'profile')
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user',
            'profile__user'
        )
        
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = _('User')
    
    def profile_link(self, obj):
        url = reverse('admin:bloger_userprofile_change', args=[obj.profile.id])
        return format_html('<a href="{}">{}</a>', url, obj.profile.user.username)
    profile_link.short_description = _('Profile')


# Optional: Register an inline for UserProfile in User admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('Profile')
    fk_name = 'user'
    fields = (
        'bio', 'profile_picture', 'career', 'location', 
        'phone', 'whatsapp_phone', 'linkedin', 'website'
    )


# User Blog Posts Inline
class UserBlogPostsInline(admin.TabularInline):
    model = BlogPost
    fk_name = 'writer'
    fields = ('title', 'status', 'created_on', 'views')
    readonly_fields = ('created_on', 'views')
    extra = 0
    show_change_link = True
    can_delete = False
    max_num = 5
    verbose_name_plural = _('Recent Blog Posts')
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_on')


# Extend UserAdmin to include the profile inline
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, UserBlogPostsInline)
    list_display = BaseUserAdmin.list_display + (
        'email', 'date_joined', 'last_login', 
        'get_followers', 'get_following', 'get_post_count'
    )
    list_filter = BaseUserAdmin.list_filter + ('is_active', 'date_joined')
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            post_count=Count('blog_posts', distinct=True)
        )

    def get_followers(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.follower_count
        return 0
    get_followers.short_description = _('Followers')

    def get_following(self, obj):
        return obj.following.count()
    get_following.short_description = _('Following')
    
    def get_post_count(self, obj):
        return getattr(obj, 'post_count', 0)
    get_post_count.short_description = _('Posts')
    get_post_count.admin_order_field = 'post_count'


# Unregister the default UserAdmin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    actions = ['export_categories_csv']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _post_count=Count('posts', distinct=True)
        )
        return queryset

    def post_count(self, obj):
        return obj._post_count
    post_count.short_description = _('Posts')
    post_count.admin_order_field = '_post_count'
    
    def export_categories_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=categories.csv'
        writer = csv.writer(response)
        
        # Add post count to the header
        writer.writerow(field_names + ['post_count'])
        
        for obj in queryset:
            # Get values for each field
            row = [getattr(obj, field) for field in field_names]
            # Add post count
            row.append(obj._post_count)
            writer.writerow(row)
            
        return response
    export_categories_csv.short_description = _("Export selected categories as CSV")


@admin.register(PostView)
class PostViewAdmin(admin.ModelAdmin):
    list_display = ('post_link', 'user_link', 'viewed_on')
    list_filter = ('viewed_on',)
    search_fields = ('post__title', 'user__username')
    raw_id_fields = ('post', 'user')
    date_hierarchy = 'viewed_on'
    readonly_fields = ('viewed_on',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'post', 'user'
        )
    
    def post_link(self, obj):
        url = reverse('admin:bloger_blogpost_change', args=[obj.post.id])
        return format_html('<a href="{}">{}</a>', url, obj.post.title)
    post_link.short_description = _('Post')
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = _('User')


# Register an admin site dashboard
from django.contrib.admin.models import LogEntry

class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag')
    list_filter = ('action_time', 'user', 'content_type')
    search_fields = ('object_repr', 'user__username')
    date_hierarchy = 'action_time'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(LogEntry, LogEntryAdmin)

# Customize the admin site header, title and index title
admin.site.site_header = _('Bloger Administration')
admin.site.site_title = _('Bloger Admin')
admin.site.index_title = _('Blog Management')