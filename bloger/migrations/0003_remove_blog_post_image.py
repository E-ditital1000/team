# Generated by Django 4.1.5 on 2023-06-01 15:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bloger', '0002_userprofile'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='blog_post',
            name='image',
        ),
    ]
