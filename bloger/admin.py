from django.contrib import admin
from .models import Blog_Post,Comment,UserProfile, Category
# Register your models here.
class Blog_PostAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug' : ('title',)}

admin.site.register(Blog_Post, Blog_PostAdmin)
admin.site.register(Comment)
admin.site.register(UserProfile)
admin.site.register(Category)