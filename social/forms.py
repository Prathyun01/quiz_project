from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, HTML, Row, Column
from django.contrib.auth import get_user_model
from .models import UserProfile, QuizShare
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, HTML, Row, Column
from django.contrib.auth import get_user_model
from .models import UserProfile, QuizShare

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'bio_extended', 'website_url', 'location',
            'show_email', 'show_quiz_history', 'show_followers', 'show_following',
            'allow_messages', 'notify_on_follow', 'notify_on_quiz_share', 'notify_on_mention'
        ]
        widgets = {
            'bio_extended': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'website_url': forms.URLInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<h5 class="mb-3">Profile Information</h5>'),
            Field('bio_extended', css_class='form-group mb-3'),
            Row(
                Column('website_url', css_class='form-group col-md-6 mb-3'),
                Column('location', css_class='form-group col-md-6 mb-3'),
            ),
            
            HTML('<h5 class="mb-3 mt-4">Privacy Settings</h5>'),
            Field('show_email', css_class='form-check mb-2'),
            Field('show_quiz_history', css_class='form-check mb-2'),
            Field('show_followers', css_class='form-check mb-2'),
            Field('show_following', css_class='form-check mb-2'),
            Field('allow_messages', css_class='form-check mb-3'),
            
            HTML('<h5 class="mb-3 mt-4">Notification Preferences</h5>'),
            Field('notify_on_follow', css_class='form-check mb-2'),
            Field('notify_on_quiz_share', css_class='form-check mb-2'),
            Field('notify_on_mention', css_class='form-check mb-3'),
            
            Submit('submit', 'Update Profile', css_class='btn btn-primary btn-lg')
        )

class QuizShareForm(forms.ModelForm):
    shared_with = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select users to share with (optional - leave empty for public share)'
    )
    
    class Meta:
        model = QuizShare
        fields = ['shared_with', 'share_message', 'is_public']
        widgets = {
            'share_message': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Add a message about why you\'re sharing this quiz...'
            }),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('share_message', css_class='form-group mb-3'),
            HTML('<h6 class="mb-3">Share With:</h6>'),
            Field('shared_with', css_class='form-group mb-3'),
            Field('is_public', css_class='form-check mb-3'),
            Submit('submit', 'Share Quiz', css_class='btn btn-success btn-lg')
        )

class SearchForm(forms.Form):
    CATEGORY_CHOICES = [
        ('', 'All Users'),
        ('active', 'Recently Active'),
        ('popular', 'Popular Users'),
        ('recent', 'New Members'),
        ('same_college', 'Same College'),
    ]
    
    query = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search users by name or username...'
        })
    )
    
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Row(
                Column('query', css_class='form-group col-md-8 mb-3'),
                Column('category', css_class='form-group col-md-4 mb-3'),
            ),
            Submit('submit', 'Search', css_class='btn btn-primary')
        )

class FollowFilterForm(forms.Form):
    FILTER_CHOICES = [
        ('all', 'All'),
        ('mutual', 'Mutual Connections'),
        ('recent', 'Recently Followed'),
        ('active', 'Most Active'),
    ]
    
    filter_type = forms.ChoiceField(
        choices=FILTER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Row(
                Column('search', css_class='form-group col-md-8'),
                Column('filter_type', css_class='form-group col-md-4'),
            ),
            Submit('submit', 'Filter', css_class='btn btn-outline-primary btn-sm')
        )
