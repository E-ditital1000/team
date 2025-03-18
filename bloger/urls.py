from django.urls import path
from . import views
from .views import (
    BlogListView, 
    DraftPostListView, 
    ProfileDetailView, 
    ProfileEditView, 
    category_detail_view
)

urlpatterns = [
    # Authentication and Profile URLs
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    # Put edit URL BEFORE the username pattern
    path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),
    path('profile/<str:username>/', ProfileDetailView.as_view(), name='profile_detail'),
    path('profile/<str:username>/follow/', views.toggle_follow, name='toggle_follow'),
    path('profile/<str:username>/like/', views.toggle_like, name='toggle_like'),
    
    # Rest of your URLs remain the same
    # Blog Post URLs
    path('', BlogListView.as_view(), name='index'),
    path('blog/create/', views.create_blog_post, name='create_blog_post'),
    path('blog/edit/<slug:slug>/', views.edit_blog_post, name='edit_blog_post'),
    path('blog/delete/<slug:slug>/', views.delete_blog_post, name='delete_blog_post'),
    path('blog/drafts/', DraftPostListView.as_view(), name='draft_posts'),
    
    # Blog Post Interaction URLs
    path('blog/like/', views.like_post, name='like_post'),
    path('like-post/', views.like_post, name='like_post'),
    path('blog/comment/<slug:slug>/', views.comment_post, name='comment_post'),
    
    # Blog Post Detail URLs - Note: Only one needed with two name aliases
    path('blog/<slug:slug>/', views.post_detail_view, name='post_detail'),
    # Use this for redirects that use the other name
    path('post/<slug:slug>/', views.post_detail_view, name='blog_detail'),
    
    # Search URLs
    path('search/', views.search_results, name='search_results'),
    
    # Category URLs
    path('category/<slug:slug>/', category_detail_view, name='category_detail'),
    
    # Informational URLs
    path('about/', views.about, name='about'),
    
    # Utility URLs
    path('set-cookie/', views.set_cookie_view, name='set_cookie'),
    path('get-cookie/', views.get_cookie_view, name='get_cookie'),
]