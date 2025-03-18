from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from .models import Message, Conversation

class MessageForm(forms.ModelForm):
    """
    Form for creating a new message in a conversation.
    """
    class Meta:
        model = Message
        fields = ['content', 'attachment']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': _('Type your message here...'),
                'class': 'form-control'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.zip'
            })
        }
        labels = {
            'content': _('Message'),
            'attachment': _('Attachment (optional)')
        }
    
    def clean_content(self):
        """
        Validate that the message content is not empty.
        """
        content = self.cleaned_data.get('content', '').strip()
        if not content and not self.cleaned_data.get('attachment'):
            raise forms.ValidationError(_('Please enter a message or attach a file.'))
        return content


class ConversationStartForm(forms.Form):
    """
    Form for starting a new conversation.
    """
    recipient = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label=_('Send message to'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': _('Type your message here...'),
            'class': 'form-control'
        }),
        label=_('Message')
    )
    attachment = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.zip'
        }),
        label=_('Attachment (optional)')
    )
    
    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Exclude the current user from recipients list
        if current_user:
            self.fields['recipient'].queryset = User.objects.exclude(id=current_user.id)
    
    def clean_content(self):
        """
        Validate that the message content is not empty.
        """
        content = self.cleaned_data.get('content', '').strip()
        if not content and not self.cleaned_data.get('attachment'):
            raise forms.ValidationError(_('Please enter a message or attach a file.'))
        return content


class UserSearchForm(forms.Form):
    """
    Form for searching users to start a new conversation.
    """
    query = forms.CharField(
        required=False,
        label='',
        widget=forms.TextInput(attrs={
            'placeholder': _('Search users...'),
            'class': 'form-control'
        })
    )