from django.shortcuts import render

# Create your views here.





from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q, Count, Max, F, OuterRef, Subquery
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _
from django.db import transaction

from .models import Conversation, Message
from .forms import MessageForm, ConversationStartForm, UserSearchForm
from django.contrib.auth.models import User

class ConversationListView(LoginRequiredMixin, ListView):
    """View for displaying all conversations for the current user."""
    model = Conversation
    template_name = 'messaging/conversation_list.html'
    context_object_name = 'conversations'
    paginate_by = 15

    def get_queryset(self):
        user = self.request.user
        
        # Get the latest message for each conversation as a subquery
        latest_message = Message.objects.filter(
            conversation=OuterRef('pk')
        ).order_by('-timestamp')
        
        # Annotate each conversation with unread count and latest message info
        queryset = Conversation.objects.filter(
            participants=user
        ).exclude(
            archived_by=user
        ).annotate(
            unread_count=Count(
                'messages',
                filter=~Q(messages__read_by=user) & ~Q(messages__sender=user)
            ),
            latest_message_time=Subquery(latest_message.values('timestamp')[:1]),
            latest_message_content=Subquery(latest_message.values('content')[:1]),
            latest_message_sender=Subquery(latest_message.values('sender__username')[:1])
        ).order_by('-updated_at')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = UserSearchForm()
        context['start_form'] = ConversationStartForm(current_user=self.request.user)
        
        # Add counts for inbox management
        user = self.request.user
        context['unread_count'] = Message.objects.filter(
            conversation__participants=user
        ).exclude(
            read_by=user
        ).exclude(
            sender=user
        ).count()
        
        context['archived_count'] = Conversation.objects.filter(
            participants=user,
            archived_by=user
        ).count()
        
        return context


class ConversationDetailView(LoginRequiredMixin, DetailView):
    """View for displaying a single conversation with its messages."""
    model = Conversation
    template_name = 'messaging/conversation_detail.html'
    context_object_name = 'conversation'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Check if user is a participant in this conversation
        if self.request.user not in obj.participants.all():
            raise PermissionDenied(_("You are not authorized to view this conversation."))
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = self.get_object()
        
        # Add messages with pagination
        messages_list = conversation.messages.select_related('sender').order_by('timestamp')
        context['message_list'] = messages_list
        
        # Add the form for sending new messages
        context['form'] = MessageForm()
        
        # Mark all messages as read
        conversation.mark_read(self.request.user)
        
        # Add other participants for display
        participants = conversation.participants.exclude(id=self.request.user.id)
        context['other_participants'] = participants
        
        return context


@login_required
@require_POST
def send_message(request, conversation_id):
    """View for sending a new message in an existing conversation."""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Verify the user is a participant
    if request.user not in conversation.participants.all():
        return HttpResponseForbidden(_("You are not authorized to send messages in this conversation."))
    
    form = MessageForm(request.POST, request.FILES)
    if form.is_valid():
        message = form.save(commit=False)
        message.conversation = conversation
        message.sender = request.user
        message.save()
        
        # Update conversation timestamp
        conversation.updated_at = timezone.now()
        conversation.save()
        
        # If the conversation was archived by any recipient, unarchive it
        for participant in conversation.participants.exclude(id=request.user.id):
            if participant in conversation.archived_by.all():
                conversation.archived_by.remove(participant)
        
        # Check if it's an AJAX request
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender': request.user.username,
                    'timestamp': message.timestamp.strftime('%b %d, %Y, %I:%M %p'),
                    'has_attachment': bool(message.attachment),
                    'attachment_url': message.attachment.url if message.attachment else None
                }
            })
        
        messages.success(request, _("Message sent successfully."))
        return redirect('conversation_detail', pk=conversation_id)
    
    # Form is invalid
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'error',
            'errors': form.errors
        }, status=400)
    
    messages.error(request, _("There was an error sending your message."))
    return redirect('conversation_detail', pk=conversation_id)


@login_required
def start_conversation(request):
    """View for starting a new conversation with another user."""
    if request.method == 'POST':
        form = ConversationStartForm(request.POST, request.FILES, current_user=request.user)
        if form.is_valid():
            recipient = form.cleaned_data['recipient']
            content = form.cleaned_data['content']
            attachment = form.cleaned_data.get('attachment')
            
            # Check if a conversation already exists between these users
            existing_conversation = Conversation.objects.annotate(
                count=Count('participants')
            ).filter(
                count=2,  # Only get one-on-one conversations
                participants=request.user
            ).filter(
                participants=recipient
            ).first()
            
            with transaction.atomic():
                if existing_conversation:
                    conversation = existing_conversation
                    # If it was archived, unarchive it
                    if request.user in conversation.archived_by.all():
                        conversation.archived_by.remove(request.user)
                else:
                    # Create a new conversation
                    conversation = Conversation.objects.create()
                    conversation.participants.add(request.user, recipient)
                
                # Create the message
                message = Message(
                    conversation=conversation,
                    sender=request.user,
                    content=content
                )
                
                if attachment:
                    message.attachment = attachment
                
                message.save()
                
                # Update conversation timestamp
                conversation.updated_at = timezone.now()
                conversation.save()
            
            messages.success(request, _("Message sent successfully."))
            return redirect('conversation_detail', pk=conversation.id)
    else:
        form = ConversationStartForm(current_user=request.user)
    
    # Get the recipient user if specified in URL
    recipient_id = request.GET.get('recipient')
    if recipient_id:
        try:
            recipient = User.objects.get(id=recipient_id)
            form.fields['recipient'].initial = recipient
        except User.DoesNotExist:
            pass
    
    return render(request, 'messaging/start_conversation.html', {
        'form': form
    })


@login_required
@require_POST
def mark_conversation_read(request, conversation_id):
    """Mark all messages in a conversation as read."""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Verify the user is a participant
    if request.user not in conversation.participants.all():
        return HttpResponseForbidden(_("You are not authorized to update this conversation."))
    
    conversation.mark_read(request.user)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('conversation_detail', pk=conversation_id)


@login_required
@require_POST
def archive_conversation(request, conversation_id):
    """Archive a conversation for the current user."""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Verify the user is a participant
    if request.user not in conversation.participants.all():
        return HttpResponseForbidden(_("You are not authorized to archive this conversation."))
    
    conversation.archived_by.add(request.user)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    messages.success(request, _("Conversation archived."))
    return redirect('conversation_list')


@login_required
@require_POST
def unarchive_conversation(request, conversation_id):
    """Unarchive a conversation for the current user."""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Verify the user is a participant
    if request.user not in conversation.participants.all():
        return HttpResponseForbidden(_("You are not authorized to unarchive this conversation."))
    
    conversation.archived_by.remove(request.user)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    messages.success(request, _("Conversation moved back to inbox."))
    return redirect('archived_conversations')


@login_required
def archived_conversations(request):
    """View for displaying archived conversations."""
    user = request.user
    
    # Get the latest message for each conversation as a subquery
    latest_message = Message.objects.filter(
        conversation=OuterRef('pk')
    ).order_by('-timestamp')
    
    # Get archived conversations with additional data
    conversations = Conversation.objects.filter(
        participants=user,
        archived_by=user
    ).annotate(
        latest_message_time=Subquery(latest_message.values('timestamp')[:1]),
        latest_message_content=Subquery(latest_message.values('content')[:1]),
        latest_message_sender=Subquery(latest_message.values('sender__username')[:1])
    ).order_by('-updated_at')
    
    return render(request, 'messaging/archived_conversations.html', {
        'conversations': conversations,
        'unread_count': Message.objects.filter(
            conversation__participants=user
        ).exclude(
            read_by=user
        ).exclude(
            sender=user
        ).count()
    })


@login_required
def search_users(request):
    """View for searching users to start a new conversation."""
    form = UserSearchForm(request.GET)
    users = []
    
    if form.is_valid() and form.cleaned_data.get('query'):
        query = form.cleaned_data['query']
        
        # Search for users by username or email
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(
            id=request.user.id  # Exclude the current user
        )[:10]  # Limit to 10 results
    
    # If it's an AJAX request, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'users': [
                {
                    'id': user.id, 
                    'username': user.username,
                    'name': f"{user.first_name} {user.last_name}".strip() or user.username
                } 
                for user in users
            ]
        })
    
    # Otherwise render template
    return render(request, 'messaging/user_search.html', {
        'form': form,
        'users': users
    })


@login_required
def user_message_status(request):
    """API view to get the unread message count for a user."""
    user = request.user
    unread_count = Message.objects.filter(
        conversation__participants=user
    ).exclude(
        read_by=user
    ).exclude(
        sender=user
    ).count()
    
    return JsonResponse({
        'unread_count': unread_count
    })