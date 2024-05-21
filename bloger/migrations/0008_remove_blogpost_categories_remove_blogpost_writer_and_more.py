# Generated by Django 5.0.6 on 2024-05-14 14:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bloger', '0007_remove_comment_image_alter_comment_commenter'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='blogpost',
            name='categories',
        ),
        migrations.RemoveField(
            model_name='blogpost',
            name='writer',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='created_on',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='birthday',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='location',
        ),
        migrations.AddField(
            model_name='comment',
            name='image',
            field=models.ImageField(default='null', upload_to='comment_images'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='commenter',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='bio',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='profile_picture',
            field=models.ImageField(default='none', upload_to='profile_img'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Blog_Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(default='null', upload_to='blog_images')),
                ('title', models.CharField(max_length=200)),
                ('body', models.TextField()),
                ('slug', models.SlugField()),
                ('created_on', models.DateTimeField(auto_now=True)),
                ('writer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='comment',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='bloger.blog_post'),
        ),
        migrations.DeleteModel(
            name='Category',
        ),
        migrations.DeleteModel(
            name='BlogPost',
        ),
    ]