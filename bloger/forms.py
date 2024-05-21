from django import forms
from .models import Comment
from .models import UserProfile
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from .models import Blog_Post, Category

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['commenter', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a comment...'}),
        }



class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'bio', 
            'profile_picture', 
            'career', 
            'nationality', 
            'birthday', 
            'linkedin', 
            'education', 
            'skills', 
            'projects', 
            'recommendations'
        ]

        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
            'education': forms.Textarea(attrs={'rows': 4}),
            'skills': forms.Textarea(attrs={'rows': 4}),
            'projects': forms.Textarea(attrs={'rows': 4}),
            'recommendations': forms.Textarea(attrs={'rows': 4}),
        }

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = Blog_Post
        fields = ['title', 'body', 'image', 'category']  # Ensure 'category' is included

    def __init__(self, *args, **kwargs):
        super(BlogPostForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].label = "Category"
        self.fields['category'].empty_label = "Select Category"