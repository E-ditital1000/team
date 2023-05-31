from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField()
    profile_picture = models.ImageField(upload_to='profile_img')

    def __str__(self):
        return self.user.username

class Blog_Post(models.Model):
    image = models.ImageField(upload_to='img')
    title = models.CharField(max_length=200)
    body = models.TextField()
    slug = models.SlugField()
    writer = models.ForeignKey(User, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Comment(models.Model):
    commenter = models.CharField(max_length=50)
    body = models.TextField()
    post = models.ForeignKey(Blog_Post, on_delete=models.CASCADE, related_name='comments')

    def __str__(self):
        return self.body