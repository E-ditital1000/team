from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('register', views.register, name='register'),
    path('login', views.login, name="login"),
    path('logout', views.logout, name="logout"),
    path('logout', views.logout, name="logout"),
    path('<str:slug>', views.blog_detail_view, name = 'blog_detail'),
    path('search/', views.search_results, name='search_results'),
    path('create/', views.create_blog_post, name='create_blog_post'),
    path('edit/<slug:slug>/', views.edit_blog_post, name='edit_blog_post'),
    path('delete/<slug:slug>/', views.delete_blog_post, name='delete_blog_post'),
    path('about/', views.about, name='about'),
]
