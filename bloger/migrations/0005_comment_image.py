# Generated by Django 4.1.5 on 2023-06-04 17:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bloger', '0004_blog_post_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='image',
            field=models.ImageField(default='null', upload_to='comment_images'),
        ),
    ]
