from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from .models import BlogPost, Comment, UserProfile, Category, PostView, ProfileLike, UserFollow

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'status_badge', 'writer_link', 'category', 
                   'created_on', 'views', 'total_likes', 'comment_count', 'featured', )
    list_filter = ('status', 'created_on', 'category', 'writer')
    search_fields = ('title', 'subtitle', 'body', 'writer__username', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('writer',)
    date_hierarchy = 'created_on'
    list_per_page = 25
    
    fieldsets = (
        (None, {
            'fields': ('title', 'subtitle', 'slug', 'writer')
        }),
        (_('Content'), {
            'fields': ('body', 'image', 'category', 'tags')
        }),
        (_('Status'), {
            'fields': ('status', 'created_on', 'published_on'),
            'classes': ('collapse',)
        }),
        (_('Metrics'), {
            'fields': ('views',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_on', 'published_on', 'views')

    def display_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    display_name.short_description = _('Name')

    def follower_count(self, obj):
        url = reverse('admin:auth_user_changelist') + f'?following__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, obj.follower_count)
    follower_count.short_description = _('Followers')

    def following_count(self, obj):
        url = reverse('admin:auth_user_changelist') + f'?user_follows__following__user__id__exact={obj.user.id}'
        return format_html('<a href="{}">{}</a>', url, obj.following_count)
    following_count.short_description = _('Following')

    def like_count(self, obj):
        url = reverse('admin:auth_user_changelist') + f'?liked_profiles__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, obj.like_count)
    like_count.short_description = _('Likes')


    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _comment_count=Count('comments', distinct=True),
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

    def comment_count(self, obj):
        return obj._comment_count
    comment_count.short_description = _('Comments')
    comment_count.admin_order_field = '_comment_count'

    def total_likes(self, obj):
        return obj.total_likes()
    total_likes.short_description = _('Likes')

    class Media:
        css = {
            'all': ('admin/css/blog_admin.css',)
        }

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('truncated_comment', 'post_link', 'commenter_link', 
                   'created_on', 'is_approved', 'is_reply')
    list_filter = ('created_on', 'is_approved', 'commenter')
    search_fields = ('body', 'commenter__username', 'post__title')
    raw_id_fields = ('post', 'commenter', 'parent')
    list_editable = ('is_approved',)
    date_hierarchy = 'created_on'
    list_per_page = 50

    def truncated_comment(self, obj):
        return obj.body[:100] + '...' if len(obj.body) > 100 else obj.body
    truncated_comment.short_description = _('Comment')

    def post_link(self, obj):
        url = reverse('admin:blog_blogpost_change', args=[obj.post.id])
        return format_html('<a href="{}">{}</a>', url, obj.post.title)
    post_link.short_description = _('Post')

    def commenter_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.commenter.id])
        return format_html('<a href="{}">{}</a>', url, obj.commenter.username)
    commenter_link.short_description = _('Commenter')

    def is_reply(self, obj):
        return bool(obj.parent)
    is_reply.boolean = True
    is_reply.short_description = _('Is Reply')


from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user_link', 
        'career', 
        'nationality', 
        'location',  # Added location
        'birthday', 
        'profile_picture_preview',
        'cover_photo_preview', 'follower_count', 'following_count', 'like_count', 'last_active'
    )
    
    search_fields = (
        'user__username', 
        'user__email', 
        'bio', 
        'career', 
        'nationality',
        'location'  # Added location to search
    )
    
    list_filter = (
        'career', 
        'nationality',
        'location', 'last_active' # Added location filter
    )
    
    raw_id_fields = ('user',)

    fieldsets = (
        (None, {
            'fields': (
                'user', 
                'bio',
                'profile_picture',
                'cover_photo'  # Added cover photo
            )
        }),
        (_('Personal Information'), {
            'fields': (
                'career', 
                'nationality', 
                'birthday', 
                'location',  # Added location
                'linkedin',
                'website'  # Added website
            )
        }),
        (_('Professional Details'), {
            'fields': (
                'education', 
                'skills', 
                'projects', 
                'recommendations'
            ),
            'classes': ('collapse',)
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = _('User')

    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="max-height: 50px; border-radius: 25px;"/>',
                obj.profile_picture.url
            )
        return _("No Image")
    profile_picture_preview.short_description = _('Profile Picture')

    def cover_photo_preview(self, obj):
        if obj.cover_photo:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px; object-fit: cover;"/>',
                obj.cover_photo.url
            )
        return _("No Cover Photo")
    cover_photo_preview.short_description = _('Cover Photo')

    # Add JSON field formatting
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['education'].widget.attrs['style'] = 'width: 90%; height: 100px; font-family: monospace;'
        form.base_fields['skills'].widget.attrs['style'] = 'width: 90%; height: 100px; font-family: monospace;'
        form.base_fields['projects'].widget.attrs['style'] = 'width: 90%; height: 100px; font-family: monospace;'
        form.base_fields['recommendations'].widget.attrs['style'] = 'width: 90%; height: 100px; font-family: monospace;'
        return form

    class Media:
        css = {
            'all': ('json_prettify.css',)
        }
        js = ('json_prettify.js',)


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
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

@admin.register(ProfileLike)
class ProfileLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile', 'created_at')
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

# Optional: Register an inline for UserProfile in User admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('Profile')
    fk_name = 'user'

# Optionally extend UserAdmin to include the profile inline
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = BaseUserAdmin.list_display + ('get_followers', 'get_following')

    def get_followers(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.follower_count
        return 0
    get_followers.short_description = _('Followers')

    def get_following(self, obj):
        return obj.following.count()
    get_following.short_description = _('Following')

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

@admin.register(PostView)
class PostViewAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'viewed_on')
    list_filter = ('viewed_on',)
    search_fields = ('post__title', 'user__username')
    raw_id_fields = ('post', 'user')
    date_hierarchy = 'viewed_on'
    readonly_fields = ('viewed_on',)