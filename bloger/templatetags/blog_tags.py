# bloger/templatetags/blog_tags.py
from django import template
from django.db.models import Count
from ..models import Category, BlogPost

register = template.Library()

@register.simple_tag
def get_categories():
    return Category.objects.annotate(
        post_count=Count('posts')  # use 'posts' instead of 'blogpost'
    ).filter(post_count__gt=0).order_by('name')


@register.simple_tag
def get_popular_posts():
    return BlogPost.objects.filter(
        status='published'
    ).order_by('-views', '-created_on')[:5]
