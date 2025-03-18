from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Conversation list and management
    path('', views.ConversationListView.as_view(), name='conversation_list'),
    path('archived/', views.archived_conversations, name='archived_conversations'),
    
    # Conversation detail and messaging
    path('conversation/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
    path('conversation/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('conversation/<int:conversation_id>/read/', views.mark_conversation_read, name='mark_conversation_read'),
    path('conversation/<int:conversation_id>/archive/', views.archive_conversation, name='archive_conversation'),
    path('conversation/<int:conversation_id>/unarchive/', views.unarchive_conversation, name='unarchive_conversation'),
    
    # Starting new conversations
    path('new/', views.start_conversation, name='start_conversation'),
    path('search-users/', views.search_users, name='search_users'),
    
    # API for notifications
    path('status/', views.user_message_status, name='user_message_status'),
]