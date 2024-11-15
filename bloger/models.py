from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField
from django.urls import reverse
from django.core.validators import MinLengthValidator, URLValidator

def validate_bio_length(value):
    word_count = len(value.split())
    if word_count > 100:
        raise ValidationError(
            _('Bio must contain no more than 100 words, but it currently contains %(count)s words.'),
            params={'count': word_count},
        )

class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(
        validators=[validate_bio_length],
        help_text=_("A brief introduction (max 100 words)")
    )
    
    cover_photo = models.ImageField(
        upload_to='cover_img/%Y/%m/',
        default='defaults/default_cover.png',
        blank=True,
        null=True,
        help_text=_("Upload a cover photo")
    )
    profile_picture = models.ImageField(
        upload_to='profile_img/%Y/%m/',
        default='defaults/default_profile.png',
        help_text=_("Upload a profile picture")
    )
    career = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Your current profession or career path")
    )
    nationality = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    birthday = models.DateField(
        null=True,
        blank=True,
        help_text=_("Your birth date (optional)")
    )
    linkedin = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        validators=[URLValidator()],
        help_text=_("Your LinkedIn profile URL")
    )
    website = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        validators=[URLValidator()],
        help_text=_("A link to your personal website or portfolio")
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Your current location (e.g., city, country)")
    )
    education = models.JSONField(
        null=True,
        blank=True,
        default=list,
        help_text=_("List of educational qualifications")
    )
    skills = models.JSONField(
        null=True,
        blank=True,
        default=list,
        help_text=_("List of professional skills")
    )
    projects = models.JSONField(
        null=True,
        blank=True,
        default=list,
        help_text=_("List of projects")
    )
    recommendations = models.JSONField(
        null=True,
        blank=True,
        default=list,
        help_text=_("Professional recommendations")
    )

    last_active = models.DateTimeField(auto_now=True)

    followers = models.ManyToManyField(
        User,
        through='UserFollow',
        related_name='following',
        blank=True,
        help_text=_("Users who follow this profile")
    )
    likes = models.ManyToManyField(
        User,
        through='ProfileLike',
        related_name='liked_profiles',
        blank=True,
        help_text=_("Users who like this profile")
    )

    @property
    def follower_count(self):
        return self.followers.count()

    @property
    def following_count(self):
        return self.user.following.count()

    @property
    def like_count(self):
        return self.likes.count()

    def is_followed_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.followers.filter(id=user.id).exists()

    def is_liked_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.likes.filter(id=user.id).exists()

    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return f"{self.user.username}'s Profile"



    def get_absolute_url(self):
        return reverse('profile_detail', kwargs={'username': self.user.username})



class UserFollow(models.Model):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_follows'
    )
    following = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='user_followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        indexes = [
            models.Index(fields=['follower', 'following']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = _("User Follow")
        verbose_name_plural = _("User Follows")

    def __str__(self):
        return f"{self.follower.username} follows {self.following.user.username}"

class ProfileLike(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='profile_likes'
    )
    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='profile_likers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'profile')
        indexes = [
            models.Index(fields=['user', 'profile']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = _("Profile Like")
        verbose_name_plural = _("Profile Likes")

    def __str__(self):
        return f"{self.user.username} likes {self.profile.user.username}'s profile"

class Category(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        validators=[MinLengthValidator(2)]
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text=_("URL-friendly version of the category name")
    )
    description = models.TextField(
        blank=True,
        help_text=_("Brief description of the category")
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        indexes = [
            models.Index(fields=['slug']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original_slug = self.slug
            counter = 1
            while Category.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})

class BlogPost(models.Model):
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('published', _('Published')),
    ]

    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(5)],
        help_text=_("Post title (minimum 5 characters)")
    )
    subtitle = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Optional subtitle for your post")
    )
    body = RichTextUploadingField(
        validators=[MinLengthValidator(100)],
        help_text=_("Main content of your post (minimum 100 characters)")
    )
    image = models.ImageField(
        upload_to='blog_images/%Y/%m/',
        null=True,
        blank=True,
        help_text=_("Featured image for the post")
    )
    writer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blog_posts'
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text=_("URL-friendly version of the title")
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft'
    )
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)
    published_on = models.DateTimeField(null=True, blank=True)
    likes = models.ManyToManyField(
        User,
        related_name='blog_post_likes',
        blank=True
    )
    views = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts'
    )
    tags = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Comma-separated tags")
    )
    featured = models.BooleanField(default=False) 

    class Meta:
        ordering = ['-created_on']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'created_on']),
            models.Index(fields=['writer']),
            models.Index(fields=['category']),
        ]
        verbose_name = _("Blog Post")
        verbose_name_plural = _("Blog Posts")

    def increment_view_count(self, user):
        if not user.is_authenticated:
            self.views += 1
            self.save(update_fields=['views'])
            return True
            
        view, created = PostView.objects.get_or_create(
            user=user,
            post=self,
            defaults={'viewed_on': timezone.now()}
        )
        if created:
            self.views += 1
            self.save(update_fields=['views'])
        return created

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while BlogPost.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        if self.status == 'published' and not self.published_on:
            self.published_on = timezone.now()
            
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'slug': self.slug})
        
    def total_likes(self):
        return self.likes.count()

    @property
    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

class Comment(models.Model):
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    commenter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    body = models.TextField(
        validators=[MinLengthValidator(5)],
        help_text=_("Your comment (minimum 5 characters)")
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='replies',
        on_delete=models.CASCADE
    )
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_on']
        indexes = [
            models.Index(fields=['post', 'created_on']),
            models.Index(fields=['commenter']),
        ]

    def __str__(self):
        return f"Comment by {self.commenter.username} on {self.post.title}"

class PostView(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_index=True
    )
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        db_index=True,
        related_name='post_views'
    )
    viewed_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        indexes = [
            models.Index(fields=['user', 'post']),
            models.Index(fields=['viewed_on']),
        ]
        verbose_name = _("Post View")
        verbose_name_plural = _("Post Views")

    def __str__(self):
        return f"{self.user.username} viewed {self.post.title}"