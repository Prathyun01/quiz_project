from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, HTML, Row, Column
from django.contrib.auth import get_user_model
from .models import Message, Conversation, ConversationSettings, MessageDraft

User = get_user_model()

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'attachment']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Type your message...',
                'maxlength': 5000
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.txt,.zip'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('content', css_class='form-group mb-3'),
            Field('attachment', css_class='form-group mb-3'),
            Submit('submit', 'Send Message', css_class='btn btn-primary')
        )

class NewConversationForm(forms.Form):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select recipient"
    )
    
    initial_message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Type your first message...'
        }),
        required=False
    )
    
    def __init__(self, current_user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude current user from recipient choices
        self.fields['recipient'].queryset = User.objects.filter(
            is_active=True,
            is_email_verified=True
        ).exclude(id=current_user.id)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('recipient', css_class='form-group mb-3'),
            Field('initial_message', css_class='form-group mb-3'),
            Submit('submit', 'Start Conversation', css_class='btn btn-primary btn-lg')
        )

class GroupConversationForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    class Meta:
        model = Conversation
        fields = ['group_name', 'group_description', 'participants']
        widgets = {
            'group_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter group name'
            }),
            'group_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional group description'
            })
        }
    
    def __init__(self, current_user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude current user from participants (they'll be added automatically)
        self.fields['participants'].queryset = User.objects.filter(
            is_active=True,
            is_email_verified=True
        ).exclude(id=current_user.id)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('group_name', css_class='form-group mb-3'),
            Field('group_description', css_class='form-group mb-3'),
            HTML('<h6 class="mb-3">Select Participants:</h6>'),
            Field('participants', css_class='form-group mb-3'),
            Submit('submit', 'Create Group', css_class='btn btn-success btn-lg')
        )

class ConversationSettingsForm(forms.ModelForm):
    class Meta:
        model = ConversationSettings
        fields = ['is_muted', 'is_archived', 'is_pinned', 'custom_notifications']
        widgets = {
            'is_muted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_archived': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'custom_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<h6 class="mb-3">Conversation Settings</h6>'),
            Field('is_muted', css_class='form-check mb-2'),
            Field('is_archived', css_class='form-check mb-2'),
            Field('is_pinned', css_class='form-check mb-2'),
            Field('custom_notifications', css_class='form-check mb-3'),
            Submit('submit', 'Save Settings', css_class='btn btn-primary')
        )

class MessageSearchForm(forms.Form):
    query = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search messages...'
        }),
        required=False
    )
    
    conversation = forms.ModelChoiceField(
        queryset=Conversation.objects.none(),
        required=False,
        empty_label="All conversations",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    message_type = forms.ChoiceField(
        choices=[('', 'All types')] + Message.MESSAGE_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['conversation'].queryset = Conversation.objects.filter(
            participants=user
        )
        
        self.helper = FormHelper()
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Row(
                Column('query', css_class='form-group col-md-6 mb-3'),
                Column('conversation', css_class='form-group col-md-3 mb-3'),
                Column('message_type', css_class='form-group col-md-3 mb-3'),
            ),
            Submit('submit', 'Search', css_class='btn btn-primary')
        )
