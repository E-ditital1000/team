# Generated by Django 5.0.6 on 2024-05-14 16:35

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bloger', '0010_remove_blog_post_likes_alter_blog_post_image_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='blog_post',
            name='likes',
            field=models.ManyToManyField(blank=True, related_name='blog_post_likes', to=settings.AUTH_USER_MODEL),
        ),
    ]
