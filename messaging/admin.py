from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count

from .models import Conversation, Message

class MessageInline(admin.TabularInline):
    """Inline view of messages within a conversation."""
    model = Message
    fields = ('sender', 'content', 'timestamp', 'attachment')
    readonly_fields = ('timestamp',)
    extra = 0
    can_delete = False
    show_change_link = True
    ordering = ('timestamp',)

    def has_add_permission(self, request, obj=None):
        # Don't allow adding messages through the admin
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin view for managing conversations."""
    list_display = ('id', 'participants_display', 'message_count', 'latest_message_display', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('participants__username', 'participants__email', 'messages__content')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MessageInline]
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        """Optimize queryset with annotations."""
        return super().get_queryset(request).prefetch_related(
            'participants', 'messages'
        ).annotate(
            msg_count=Count('messages')
        )
    
    def participants_display(self, obj):
        """Display participants as a clickable list."""
        participants = obj.participants.all()
        return format_html(
            ', '.join(
                f'<a href="/admin/auth/user/{user.id}/change/">{user.username}</a>'
                for user in participants
            )
        )
    participants_display.short_description = _("Participants")
    participants_display.admin_order_field = 'participants__username'
    
    def message_count(self, obj):
        """Display the number of messages in the conversation."""
        return getattr(obj, 'msg_count', obj.messages.count())
    message_count.short_description = _("Messages")
    message_count.admin_order_field = 'msg_count'
    
    def latest_message_display(self, obj):
        """Display the latest message in the conversation."""
        latest = obj.messages.order_by('-timestamp').first()
        if latest:
            # Truncate message content for display
            content = latest.content[:50] + ('...' if len(latest.content) > 50 else '')
            return format_html(
                '{}: "{}" <span class="text-muted">at {}</span>',
                latest.sender.username,
                content,
                latest.timestamp.strftime('%Y-%m-%d %H:%M')
            )
        return _("No messages")
    latest_message_display.short_description = _("Latest Message")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin view for managing individual messages."""
    list_display = ('id', 'sender_display', 'conversation_link', 'short_content', 'has_attachment', 'timestamp')
    list_filter = ('timestamp', 'sender', 'read_by')
    search_fields = ('content', 'sender__username', 'conversation__id')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    raw_id_fields = ('conversation', 'sender', 'read_by')
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related."""
        return super().get_queryset(request).select_related(
            'conversation', 'sender'
        ).prefetch_related('read_by')
    
    def sender_display(self, obj):
        """Display sender as a link to their admin page."""
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.sender.id,
            obj.sender.username
        )
    sender_display.short_description = _("Sender")
    sender_display.admin_order_field = 'sender__username'
    
    def short_content(self, obj):
        """Display truncated message content."""
        return obj.content[:100] + ('...' if len(obj.content) > 100 else '')
    short_content.short_description = _("Content")
    
    def has_attachment(self, obj):
        """Display a checkmark if the message has an attachment."""
        return bool(obj.attachment)
    has_attachment.boolean = True
    has_attachment.short_description = _("Attachment")
    
    def conversation_link(self, obj):
        """Display a link to the conversation admin page."""
        return format_html(
            '<a href="/admin/messaging/conversation/{}/change/">Conversation #{}</a>',
            obj.conversation.id,
            obj.conversation.id
        )
    conversation_link.short_description = _("Conversation")
    conversation_link.admin_order_field = 'conversation__id'