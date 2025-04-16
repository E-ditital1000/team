"""
Project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),
    
    # Main applications
    path('', include('bloger.urls')),
    path('shop/', include('shop.urls', namespace='shop')),  # Shop app URLs
    path('chats/', include('chats.urls', namespace='chats')),  # chats app URLs
    
    # CKEditor - ensure this is included
    path("ckeditor5/", include('django_ckeditor_5.urls')),
    path('select2/', include('django_select2.urls')),  # Add this line
]

# Handling static and media files
if settings.DEBUG:
    # In development, use Django's static and media serving
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # In production, ensure correct serving of media and static files
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT
        }),
        re_path(r'^static/(?P<path>.*)$', serve, {
            'document_root': settings.STATIC_ROOT
        }),
    ]