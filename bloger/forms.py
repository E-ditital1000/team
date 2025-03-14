
from django import forms
import bleach
from django_ckeditor_5.widgets import CKEditor5Widget
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

        # Ensure a minimum length
        if len(body.strip()) < 5:
            raise ValidationError(_('Comment must be at least 5 characters long.'))

        # Sanitize the input with Bleach
        allowed_tags = ['p', 'b', 'i', 'u', 'strong', 'em', 'a']
        allowed_attrs = {'a': ['href', 'title', 'target']}

        body = bleach.clean(
            body,
            tags=allowed_tags,
            attributes=allowed_attrs,
            strip=True
        )

        return body

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import UserProfile
import json
import re

class UserProfileForm(forms.ModelForm):
    """
    Enhanced form for editing user profile information
    Includes personal details, contact information, and seller-specific fields
    """
    
    # Define field groups for better organization in templates
    PERSONAL_INFO_FIELDS = ['bio', 'profile_picture', 'cover_photo', 'birthday', 'nationality', 'location']
    PROFESSIONAL_INFO_FIELDS = ['career', 'education', 'skills', 'work_experience', 'projects']
    CONTACT_INFO_FIELDS = ['phone', 'whatsapp_phone', 'email', 'linkedin', 'website']
    BUSINESS_INFO_FIELDS = ['business_name', 'business_address', 'receive_order_emails', 'receive_order_whatsapp']
    
    # Add a read-only email field to display user's email
    email = forms.EmailField(
        required=False,
        disabled=True,
        help_text=_("Email address cannot be changed here. Contact support for email changes.")
    )
    
    class Meta:
        model = UserProfile
        fields = [
            # Personal Information
            'bio',
            'profile_picture',
            'cover_photo',  
            'birthday',
            'nationality',
            'location',
            
            # Professional Information
            'career',
            'education',
            'skills',
            'work_experience',
            'projects',
            'recommendations',
            
            # Contact Information
            'phone',
            'whatsapp_phone',
            'linkedin',
            'website',
            
            # Business Information (for Sellers)
            'business_name',
            'business_address',
            'receive_order_emails',
            'receive_order_whatsapp',
        ]
        
        widgets = {
            # Personal Information
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': _('Tell us about yourself (max 100 words)'),
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'cover_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'birthday': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'nationality': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Your nationality')
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('City, Country')
            }),
            
            # Professional Information
            'career': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Your current profession or business')
            }),
            'education': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control json-input',
                'placeholder': _('Enter your education history in JSON format'),
            }),
            'skills': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control json-input',
                'placeholder': _('Enter your skills in JSON format'),
            }),
            'work_experience': forms.Textarea(attrs={
                'rows': 4, 
                'class': 'form-control json-input',
                'placeholder': _('Enter your work experience in JSON format'),
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
            
            # Contact Information
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('+1234567890'),
                'pattern': '^\+?[0-9\s\-\(\)]{7,20}$',
                'title': _('Enter a valid phone number with country code (e.g., +1234567890)')
            }),
            'whatsapp_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('+1234567890'),
                'pattern': '^\+?[0-9\s\-\(\)]{7,20}$',
                'title': _('Enter a valid WhatsApp number with country code (e.g., +1234567890)')
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/username'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            
            # Business Information
            'business_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Your business or store name')
            }),
            'business_address': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': _('Full business address including postal code')
            }),
            'receive_order_emails': forms.CheckboxInput(attrs={
                'class': 'form-check-input me-2'
            }),
            'receive_order_whatsapp': forms.CheckboxInput(attrs={
                'class': 'form-check-input me-2'
            }),
        }
        
        help_texts = {
            # Personal Information
            'bio': _('Introduce yourself briefly to other users (100 words maximum)'),
            'profile_picture': _('Upload a professional profile image (recommended size: 400x400px)'),
            'cover_photo': _('Upload a cover image for your profile page (recommended size: 1200x300px)'),
            'birthday': _('Your birthdate (only the year will be visible to others)'),
            'nationality': _('Your country of origin'),
            'location': _('Your current location (city and country)'),
            
            # Professional Information
            'career': _('Your current professional role or business'),
            'education': _('Example format: [{"degree": "Bachelor\'s", "institution": "University", "start_year": 2020, "end_year": 2024}]'),
            'skills': _('Example format: [{"name": "Python Programming", "level": "Advanced"}, {"name": "Project Management", "level": "Intermediate"}]'),
            'work_experience': _('Example format: [{"title": "Software Developer", "company": "Tech Corp", "start_date": "2020-01", "end_date": "2022-12", "description": "Developed web applications"}]'),
            'projects': _('Example format: [{"title": "Project Name", "description": "Project details", "url": "https://project-url.com", "status": "In progress"}]'),
            'recommendations': _('Example format: [{"recommender_name": "John Doe", "relationship": "Supervisor", "recommendation": "Strongly recommended"}]'),
            
            # Contact Information
            'phone': _('Your contact phone number with country code (e.g., +1234567890)'),
            'whatsapp_phone': _('Your WhatsApp number for order notifications (e.g., +1234567890)'),
            'linkedin': _('Your LinkedIn profile URL'),
            'website': _('Your personal website or portfolio URL'),
            
            # Business Information
            'business_name': _('The name of your business or store (visible to customers)'),
            'business_address': _('Your business address (for shipping and administrative purposes)'),
            'receive_order_emails': _('Receive email notifications when customers place orders'),
            'receive_order_whatsapp': _('Receive WhatsApp messages when customers place orders'),
        }
        
        labels = {
            # Personal Information
            'bio': _('About Me'),
            'profile_picture': _('Profile Picture'),
            'cover_photo': _('Cover Photo'),
            'birthday': _('Birth Date'),
            'nationality': _('Nationality'),
            'location': _('Current Location'),
            
            # Professional Information
            'career': _('Profession'),
            'education': _('Education History'),
            'skills': _('Skills & Expertise'),
            'work_experience': _('Work Experience'),
            'projects': _('Projects'),
            'recommendations': _('Recommendations'),
            
            # Contact Information
            'phone': _('Phone Number'),
            'whatsapp_phone': _('WhatsApp Number'),
            'linkedin': _('LinkedIn Profile'),
            'website': _('Website'),
            
            # Business Information
            'business_name': _('Business/Store Name'),
            'business_address': _('Business Address'),
            'receive_order_emails': _('Receive Order Emails'),
            'receive_order_whatsapp': _('Receive Order WhatsApp Messages'),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.get('instance', None)
        if user and hasattr(user, 'user'):
            self.user = user.user
        else:
            self.user = None
            
        super().__init__(*args, **kwargs)
        
        # Fill the email field with the user's email if available
        if self.user:
            self.fields['email'].initial = self.user.email
            
        # Mark required fields
        for field_name, field in self.fields.items():
            if field.required:
                self.fields[field_name].label = f"{field.label} *"
                
        # Add seller section only for users who are selling products
        if self.user and not self.user.products.exists():
            # Hide business fields for non-sellers
            for field in self.BUSINESS_INFO_FIELDS:
                if field in self.fields:
                    self.fields[field].widget = forms.HiddenInput()

    # Validation methods
    def clean_bio(self):
        """Validate bio length"""
        bio = self.cleaned_data.get('bio')
        if not bio:
            return bio
        word_count = len(bio.split())
        if word_count > 100:
            raise ValidationError(_('Bio must not exceed 100 words.'))
        return bio

    def clean_phone(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone')
        if not phone:
            return phone
            
        # Remove spaces, dashes, parentheses
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Ensure it starts with + and contains 7-15 digits
        if not re.match(r'^\+?[0-9]{7,15}$', cleaned_phone):
            raise ValidationError(_('Enter a valid phone number with country code (e.g., +1234567890)'))
            
        # Ensure it has a country code (starts with +)
        if not cleaned_phone.startswith('+'):
            cleaned_phone = '+' + cleaned_phone
            
        return cleaned_phone
        
    def clean_whatsapp_phone(self):
        """Validate WhatsApp number format"""
        whatsapp = self.cleaned_data.get('whatsapp_phone')
        if not whatsapp:
            return whatsapp
            
        # Remove spaces, dashes, parentheses
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', whatsapp)
        
        # Ensure it starts with + and contains 7-15 digits
        if not re.match(r'^\+?[0-9]{7,15}$', cleaned_phone):
            raise ValidationError(_('Enter a valid WhatsApp number with country code (e.g., +1234567890)'))
            
        # Ensure it has a country code (starts with +)
        if not cleaned_phone.startswith('+'):
            cleaned_phone = '+' + cleaned_phone
            
        return cleaned_phone

    def clean_linkedin(self):
        """Ensure LinkedIn URL has proper format"""
        linkedin = self.cleaned_data.get('linkedin')
        if not linkedin:
            return linkedin
            
        # Add https:// if missing
        if not linkedin.startswith(('http://', 'https://')):
            linkedin = 'https://' + linkedin
            
        # Validate it's a LinkedIn URL
        if 'linkedin.com' not in linkedin:
            raise ValidationError(_('Please enter a valid LinkedIn profile URL'))
            
        return linkedin

    def clean_website(self):
        """Ensure website URL has proper format"""
        website = self.cleaned_data.get('website')
        if not website:
            return website
            
        # Add https:// if missing
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
            
        return website

    def clean_json_field(self, field_name):
        """Generic method to validate and clean JSON fields"""
        data = self.cleaned_data.get(field_name)
        if not data:
            return []
            
        # If already a list/dict, return as is
        if not isinstance(data, str):
            return data
            
        # Try to parse JSON string
        try:
            parsed_data = json.loads(data)
            
            # Ensure it's a list
            if not isinstance(parsed_data, list):
                raise ValidationError(_('Data must be a JSON array/list'))
                
            return parsed_data
        except json.JSONDecodeError:
            raise ValidationError(_('Invalid JSON format. Please check the example format.'))

    # Clean methods for JSON fields
    def clean_education(self):
        return self.clean_json_field('education')

    def clean_skills(self):
        return self.clean_json_field('skills')

    def clean_projects(self):
        return self.clean_json_field('projects')
        
    def clean_work_experience(self):
        return self.clean_json_field('work_experience')

    def clean_recommendations(self):
        return self.clean_json_field('recommendations')
        
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        
        # If WhatsApp notifications are enabled, require a WhatsApp number
        receive_whatsapp = cleaned_data.get('receive_order_whatsapp')
        whatsapp_phone = cleaned_data.get('whatsapp_phone')
        
        if receive_whatsapp and not whatsapp_phone:
            self.add_error('whatsapp_phone', 
                _('WhatsApp number is required if you want to receive order notifications via WhatsApp'))
                
        # Use regular phone as WhatsApp if whatsapp_phone is not provided
        phone = cleaned_data.get('phone')
        if not whatsapp_phone and phone and receive_whatsapp:
            cleaned_data['whatsapp_phone'] = phone
            
        return cleaned_data

    class Media:
        js = ('js/json_editor.js',)
        css = {
            'all': ('css/profile_form.css',)
        }


from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import BlogPost, Category

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'subtitle', 'body', 'image', 'category', 'tags', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter post title (minimum 5 characters)'),
            }),
            'subtitle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter optional subtitle'),
            }),
            'body': CKEditor5Widget(
                config_name='default',
                attrs={
                    'class': 'django_ckeditor_5',
                }
            ),
            'image': forms.FileInput(attrs={
                'class': 'form-control custom-file-input',
                'accept': 'image/*',
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter tags separated by commas'),
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get categories with ordering
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        self.fields['category'].empty_label = _("Select Category")
        
        # Add required field indicators
        self.fields['title'].required = True
        self.fields['body'].required = True
        self.fields['category'].required = True
        self.fields['status'].required = True
        
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
        # Strip HTML tags for length validation
        from django.utils.html import strip_tags
        body_text = strip_tags(body)
        if len(body_text.strip()) < 100:
            raise ValidationError(_('Content must be at least 100 characters long.'))
        return body

    class Media:
        css = {
            'all': [
                'django_ckeditor_5/dist/styles.css',
            ]
        }
        js = [
            'django_ckeditor_5/dist/bundle.js',
        ]
    
    

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