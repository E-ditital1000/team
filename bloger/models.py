from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

def validate_bio_length(value):
    word_count = len(value.split())
    if word_count > 100:
        raise ValidationError(
            _('Bio must contain no more than 100 words, but it currently contains %(count)s words.'),
            params={'count': word_count},
        )

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(validators=[validate_bio_length])
    profile_picture = models.ImageField(upload_to='profile_img', default='none')
    career = models.CharField(max_length=100, blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    birthday = models.DateField(null=True, blank=True)
    linkedin = models.URLField(max_length=200, blank=True, null=True)
    education = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    projects = models.TextField(blank=True, null=True)
    recommendations = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.username

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        # Generate slug only if it does not exist
        if not self.slug:
            self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.slug})"


class Blog_Post(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    image = models.ImageField(upload_to='blog_images', null=True, blank=True)
    writer = models.ForeignKey(User, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    created_on = models.DateTimeField(default=timezone.now)
    likes = models.ManyToManyField(User, related_name='blog_post_likes', blank=True)
    views = models.IntegerField(default=0)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)  # ForeignKey to Category

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            num = 1
            while Blog_Post.objects.filter(slug=self.slug).exists():
                self.slug = '{}-{}'.format(original_slug, num)
                num += 1
        super(Blog_Post, self).save(*args, **kwargs)

    def __str__(self):
        return self.title
        
    def total_likes(self):
        return self.likes.count()

    def increment_view_count(self):
        self.views += 1
        self.save(update_fields=['views'])

class Comment(models.Model):
    post = models.ForeignKey(Blog_Post, on_delete=models.CASCADE, related_name='comments')
    commenter = models.CharField(max_length=50)
    body = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    created_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.body