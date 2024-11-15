from django.urls import path
from . import views
from .views import category_detail_view, ProfileEditView
from .views import BlogListView, about 
from .views import DraftPostListView

urlpatterns = [
    # Authentication and Profile URLs
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),
   # Ensure this URL pattern exists

    # Blog Post URLs
    path('', BlogListView.as_view(), name='index'), 
    path('create/', views.create_blog_post, name='create_blog_post'),
    path('edit/<slug:slug>/', views.edit_blog_post, name='edit_blog_post'),
    path('delete/<slug:slug>/', views.delete_blog_post, name='delete_blog_post'),  # Ensure you have this view implemented
    path('search/', views.search_results, name='search_results'),
    path('like_post/', views.like_post, name='like_post'),
    path('comment/<slug:slug>/', views.comment_post, name='comment_post'),
    path('post/<slug:slug>/', views.post_detail_view, name='post_detail'),
    path('post/<slug:slug>/', views.post_detail_view, name='blog_detail'),
    path('drafts/', DraftPostListView.as_view(), name='draft_posts'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.ProfileDetailView.as_view(), name='profile_detail'),
path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),
path('profile/<str:username>/follow/', views.toggle_follow, name='toggle_follow'),
path('profile/<str:username>/like/', views.toggle_like, name='toggle_like'),

    

   
    # Informational URLs
    path('about/', views.about, name='about'),

    # Blog Detail URLs
   # Place this after more specific paths

    # Category Detail URLs
    path('category/<slug:slug>/', category_detail_view, name='category_detail'),

    # Cookie Test URLs
    path('set-cookie/', views.set_cookie_view, name='set_cookie'),
    path('get-cookie/', views.get_cookie_view, name='get_cookie'),
]
