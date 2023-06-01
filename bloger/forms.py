from django import forms
from .models import Comment
from .models import UserProfile
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from .models import Blog_Post


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['commenter', 'body']



class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture']

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = Blog_Post
        fields = ['title', 'body', 'slug']