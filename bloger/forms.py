from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import BlogPost, Category, Comment, UserProfile

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': _('Add a comment... (minimum 5 characters)'),
                'class': 'form-control',
            }),
        }

    def clean_body(self):
        body = self.cleaned_data.get('body')
        if len(body.strip()) < 5:
            raise ValidationError(_('Comment must be at least 5 characters long.'))
        return body

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'bio',
            'profile_picture',
            'cover_photo',  # Added
            'career',
            'nationality',
            'birthday',
            'linkedin',
            'website',  # Added
            'location',  # Added
            'education',
            'skills',
            'projects',
            'recommendations',
            'work_experience'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': _('Tell us about yourself (max 100 words)'),
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'cover_photo': forms.FileInput(attrs={  # Added
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'career': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Your current profession')
            }),
            'nationality': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'location': forms.TextInput(attrs={  # Added
                'class': 'form-control',
                'placeholder': _('City, Country')
            }),
            'birthday': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/username'
            }),
            'website': forms.URLInput(attrs={  # Added
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'education': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control json-input',  # Added json-input class
                'placeholder': _('Enter your education history in JSON format'),
            }),
            'skills': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control json-input',
                'placeholder': _('Enter your skills in JSON format'),
            }),
            'projects': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control json-input',
                'placeholder': _('Enter your projects in JSON format'),
            }),
            'recommendations': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control json-input',
                'placeholder': _('Enter recommendations in JSON format'),
            }),
        }
        help_texts = {
            'education': _('Example format: [{"degree": "Bachelor\'s", "institution": "University", "start_year": 2020, "end_year": 2024}]'),
            'skills': _('Example format: ["name", "Python Programming", "level": "Advanced"]'),
            'projects': _('Example format: [{"title": "Project Name", "description": "Project details", "url": "https://project-url.com", "status": "In progress"}]'),
            'recommendations': _('Example format: [{"recommender_name": "John Doe", "relationship": "Supervisor", "recommendation": "Strongly recommended"}]'),
            'website': _('Enter the full URL of your personal website or portfolio'),
            'location': _('Enter your current city and country'),
        }

    def clean_linkedin(self):
        linkedin = self.cleaned_data.get('linkedin')
        if linkedin and not linkedin.startswith(('http://', 'https://')):
            linkedin = 'https://' + linkedin
        return linkedin

    def clean_website(self):  # Added
        website = self.cleaned_data.get('website')
        if website and not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        return website

    def clean_bio(self):
        bio = self.cleaned_data.get('bio')
        if not bio:
            return bio
        word_count = len(bio.split())
        if word_count > 100:
            raise ValidationError(_('Bio must not exceed 100 words.'))
        return bio

    def clean_json_field(self, field_name):  # Added
        data = self.cleaned_data.get(field_name)
        if not data:
            return []
        try:
            if isinstance(data, str):
                import json
                return json.loads(data)
            return data
        except json.JSONDecodeError:
            raise ValidationError(_('Invalid JSON format. Please check the example format.'))

    def clean_education(self):
        return self.clean_json_field('education')

    def clean_skills(self):
        return self.clean_json_field('skills')

    def clean_projects(self):
        return self.clean_json_field('projects')

    def clean_recommendations(self):
        return self.clean_json_field('recommendations')

    class Media:
        js = ('js/json_prettify.js',)  # Add this file to your static files
        css = {
            'all': ('css/json_prettify.css',)
        }

class BlogPostForm(forms.ModelForm):
    ...
    class Meta:
        model = BlogPost
        fields = [
            'title', 'subtitle', 'body', 'image', 'category', 'tags', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter post title (minimum 5 characters)'),
            }),
            'subtitle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter optional subtitle'),
            }),
            # No need to specify widget for body, CKEditor will handle this.
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        super(BlogPostForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        self.fields['category'].empty_label = _("Select Category")
        
        # If we're editing an existing post, populate the tags field
        if self.instance.pk and self.instance.tags:
            self.initial['tags'] = self.instance.tags

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title.strip()) < 5:
            raise ValidationError(_('Title must be at least 5 characters long.'))
        return title

    def clean_body(self):
        body = self.cleaned_data.get('body')
        if len(body.strip()) < 100:
            raise ValidationError(_('Content must be at least 100 characters long.'))
        return body

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter category name'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Enter category description'),
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name.strip()) < 2:
            raise ValidationError(_('Category name must be at least 2 characters long.'))
        return name