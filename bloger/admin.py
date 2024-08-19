from django.contrib import admin
from .models import Blog_Post, Comment, UserProfile, Category

class Blog_PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'writer', 'created_on', 'views', 'total_likes')  # Display these fields in the list view
    list_filter = ('created_on', 'writer', 'category')  # Add filters for these fields
    search_fields = ('title', 'body', 'writer__username')  # Enable search functionality
    prepopulated_fields = {'slug': ('title',)}  # Automatically populate slug field

    def total_likes(self, obj):
        return obj.likes.count()

class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'commenter', 'created_on')  # Display these fields in the list view
    list_filter = ('created_on', 'commenter')  # Add filters for these fields
    search_fields = ('commenter__username', 'body')  # Enable search functionality

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio')  # Display these fields in the list view
    search_fields = ('user__username', 'bio')  # Enable search functionality

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)  # Display category names in the list view
    search_fields = ('name',)  # Enable search functionality

# Register your models with the customized admin classes
admin.site.register(Blog_Post, Blog_PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Category, CategoryAdmin)
