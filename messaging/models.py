from django.db import models

# Create your models here.


from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse

class Conversation(models.Model):
    """
    Represents a conversation between two users.
    Can be expanded to group conversations in the future.
    """
    participants = models.ManyToManyField(
        User,
        related_name='conversations',
        help_text=_("Users participating in this conversation")
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    # For tracking if a conversation has been archived
    archived_by = models.ManyToManyField(
        User,
        related_name='archived_conversations',
        blank=True,
        help_text=_("Users who have archived this conversation")
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _("Conversation")
        verbose_name_plural = _("Conversations")
        indexes = [
            models.Index(fields=['-updated_at'])
        ]

    def get_messages(self):
        """Return all messages in this conversation, ordered by timestamp."""
        return self.messages.all().order_by('timestamp')
    
    def get_latest_message(self):
        """Return the most recent message in this conversation."""
        return self.messages.order_by('-timestamp').first()
    
    def unread_count_for(self, user):
        """Return the number of unread messages for a specific user."""
        return self.messages.filter(read_by__isnull=True).exclude(sender=user).count()
    
    def mark_read(self, user):
        """Mark all messages in the conversation as read for a specific user."""
        unread_messages = self.messages.filter(read_by__isnull=True).exclude(sender=user)
        for message in unread_messages:
            message.read_by.add(user)
    
    def add_message(self, user, content):
        """Add a new message to the conversation."""
        message = Message.objects.create(
            conversation=self,
            sender=user,
            content=content
        )
        self.updated_at = timezone.now()
        self.save()
        return message
    
    def get_absolute_url(self):
        """URL for viewing the conversation."""
        return reverse('conversation_detail', kwargs={'pk': self.pk})

    def __str__(self):
        """String representation of the conversation."""
        participants = self.participants.all()
        if participants.count() <= 3:  # Only show names for small conversations
            names = ", ".join([str(user.username) for user in participants])
            return f"Conversation between {names}"
        else:
            return f"Conversation with {participants.count()} participants"


class Message(models.Model):
    """
    Represents a single message within a conversation.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text=_("The conversation this message belongs to")
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text=_("User who sent this message")
    )
    content = models.TextField(
        help_text=_("The message content")
    )
    timestamp = models.DateTimeField(default=timezone.now)
    read_by = models.ManyToManyField(
        User,
        related_name='read_messages',
        blank=True,
        help_text=_("Users who have read this message")
    )
    # For potentially storing attachments later
    attachment = models.FileField(
        upload_to='message_attachments/%Y/%m/',
        null=True,
        blank=True,
        help_text=_("Optional file attachment")
    )

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['sender']),
        ]
    
    def is_read_by(self, user):
        """Check if the message has been read by a specific user."""
        return user in self.read_by.all()
    
    def mark_as_read(self, user):
        """Mark this message as read by a specific user."""
        if user != self.sender and user not in self.read_by.all():
            self.read_by.add(user)
    
    def __str__(self):
        """String representation of the message."""
        return f"Message from {self.sender.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"