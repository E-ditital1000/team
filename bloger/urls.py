

from django.urls import path
from . import views
from .views import category_detail_view

urlpatterns = [
    path('profile/edit/',  views.ProfileEditView.as_view(), name='profile_edit'),
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name="login"),
    path('logout/', views.logout, name="logout"),
    path('like_post/', views.like_post, name='like_post'),
    path('create/', views.create_blog_post, name='create_blog_post'),  # This should come before the slug path
    path('search/', views.search_results, name='search_results'),
    path('edit/<slug:slug>/', views.edit_blog_post, name='edit_blog_post'),
    path('delete/<slug:slug>/', views.delete_blog_post, name='delete_blog_post'),
    path('about/', views.about, name='about'),
    path('<slug:slug>/', views.blog_detail_view, name='blog_detail'),  # Make sure this is after all specific paths
    path('set-cookie/', views.set_cookie_view, name='set_cookie'),
    path('get-cookie/', views.get_cookie_view, name='get_cookie'),
    path('category/<slug:slug>/', category_detail_view, name='category_detail'),
]
