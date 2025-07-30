from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, HTML, Row, Column, Div
from crispy_forms.bootstrap import InlineRadios
from .models import CustomUser, College

class UserRegistrationForm(UserCreationForm):
    """Enhanced user registration form with additional fields"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        help_text='We will send a verification code to this email.'
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    
    college = forms.ModelChoiceField(
        queryset=College.objects.filter(is_active=True),
        required=False,
        empty_label="Select your college (optional)",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    year_of_study = forms.ChoiceField(
        choices=[('', 'Select year of study')] + CustomUser.YEAR_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number (optional)'
        })
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='I agree to the Terms of Service and Privacy Policy'
    )

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'college', 'year_of_study', 'phone_number',
            'password1', 'password2', 'terms_accepted'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Create a strong password'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Confirm your password'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            HTML('<h3 class="text-glass mb-4 text-center">Create Your Account</h3>'),
            
            # Personal Information
            HTML('<h6 class="text-glass mb-3">Personal Information</h6>'),
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
            ),
            Field('email', css_class='form-group mb-3'),
            Field('phone_number', css_class='form-group mb-3'),
            
            # Academic Information
            HTML('<h6 class="text-glass mb-3 mt-4">Academic Information</h6>'),
            Field('college', css_class='form-group mb-3'),
            Field('year_of_study', css_class='form-group mb-3'),
            
            # Account Information
            HTML('<h6 class="text-glass mb-3 mt-4">Account Information</h6>'),
            Field('username', css_class='form-group mb-3'),
            Field('password1', css_class='form-group mb-3'),
            Field('password2', css_class='form-group mb-3'),
            
            # Terms and Submit
            Field('terms_accepted', css_class='form-check mb-4'),
            
            Submit('submit', 'Create Account', css_class='btn btn-3d btn-lg w-100')
        )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists
            if CustomUser.objects.filter(email=email).exists():
                raise ValidationError('An account with this email already exists.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check if username already exists
            if CustomUser.objects.filter(username=username).exists():
                raise ValidationError('This username is already taken.')
            # Username validation
            if len(username) < 3:
                raise ValidationError('Username must be at least 3 characters long.')
        return username

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Basic phone number validation
            phone = phone.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if not phone.isdigit():
                raise ValidationError('Please enter a valid phone number.')
            if len(phone) < 10:
                raise ValidationError('Phone number must be at least 10 digits.')
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        
        if commit:
            user.save()
            # Set additional fields after saving
            user.college = self.cleaned_data.get('college')
            user.year_of_study = self.cleaned_data.get('year_of_study', '')
            user.save()
        return user

class CustomLoginForm(AuthenticationForm):
    """Login form accepting email or username"""
    
    username = forms.CharField(
        label='Email or Username',
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email or username',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('username', css_class='form-group mb-3'),
            Field('password', css_class='form-group mb-3'),
            Submit('submit', 'Sign In', css_class='btn btn-3d btn-lg w-100')
        )

    def clean(self):
        username_or_email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username_or_email is not None and password:
            # Use custom authentication
            self.user_cache = authenticate(
                self.request,
                username=username_or_email,
                password=password
            )
            
            if self.user_cache is None:
                raise ValidationError(
                    "Please enter a correct email/username and password.",
                    code='invalid_login',
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        """Allow login for active users"""
        if not user.is_active:
            raise ValidationError(
                "This account is inactive.",
                code='inactive',
            )    
        if not user.is_email_verified:
            raise ValidationError(
                "Please verify your email address before logging in. Check your inbox for the verification code.",
                code='unverified_email',
            )

class EmailVerificationForm(forms.Form):
    """OTP verification form with enhanced validation"""
    
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control otp-input text-center',
            'placeholder': '000000',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'style': 'letter-spacing: 0.5em; font-size: 1.8rem; font-weight: bold;'
        }),
        label='Verification Code',
        help_text='Enter the 6-digit code sent to your email'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('otp', css_class='form-group mb-4 text-center'),
            Submit('submit', 'Verify Email', css_class='btn btn-3d btn-lg w-100')
        )

    def clean_otp(self):
        otp = self.cleaned_data.get('otp')
        if otp:
            # Remove any spaces or non-digit characters
            otp = ''.join(filter(str.isdigit, otp))
            
            if len(otp) != 6:
                raise ValidationError('Please enter exactly 6 digits.')
            
            if not otp.isdigit():
                raise ValidationError('Please enter only numbers.')
                
        return otp

class UserProfileForm(forms.ModelForm):
    """User profile update form"""
    
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Tell us about yourself...'
        }),
        help_text='Optional bio (max 500 characters)'
    )
    
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'username',
            'phone_number', 'bio', 'date_of_birth',
            'college', 'year_of_study', 'profile_picture',
            'twitter_url', 'linkedin_url', 'github_url',
            'is_profile_public', 'email_notifications'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': True}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'college': forms.Select(attrs={'class': 'form-control'}),
            'year_of_study': forms.Select(attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://twitter.com/username'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/username'}),
            'github_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/username'}),
            'is_profile_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            HTML('<h4 class="text-glass mb-4">Personal Information</h4>'),
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('email', css_class='form-group col-md-6 mb-3'),
                Column('username', css_class='form-group col-md-6 mb-3'),
            ),
            Field('phone_number', css_class='form-group mb-3'),
            Field('bio', css_class='form-group mb-3'),
            Field('date_of_birth', css_class='form-group mb-3'),
            
            HTML('<h4 class="text-glass mb-4 mt-4">Academic Information</h4>'),
            Row(
                Column('college', css_class='form-group col-md-6 mb-3'),
                Column('year_of_study', css_class='form-group col-md-6 mb-3'),
            ),
            
            HTML('<h4 class="text-glass mb-4 mt-4">Profile Picture</h4>'),
            Field('profile_picture', css_class='form-group mb-3'),
            
            HTML('<h4 class="text-glass mb-4 mt-4">Social Media Links</h4>'),
            Field('twitter_url', css_class='form-group mb-3'),
            Field('linkedin_url', css_class='form-group mb-3'),
            Field('github_url', css_class='form-group mb-3'),
            
            HTML('<h4 class="text-glass mb-4 mt-4">Privacy Settings</h4>'),
            Field('is_profile_public', css_class='form-check mb-3'),
            Field('email_notifications', css_class='form-check mb-4'),
            
            Submit('submit', 'Update Profile', css_class='btn btn-3d btn-lg w-100')
        )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Don't allow email changes for now
        if self.instance and self.instance.email != email:
            raise ValidationError('Email address cannot be changed. Contact support if needed.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Don't allow username changes for now
        if self.instance and self.instance.username != username:
            raise ValidationError('Username cannot be changed. Contact support if needed.')
        return username

class PasswordChangeForm(forms.Form):
    """Custom password change form"""
    
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        }),
        label='Current Password'
    )
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your new password'
        }),
        label='New Password',
        help_text='Password must be at least 8 characters long.'
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your new password'
        }),
        label='Confirm New Password'
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('old_password', css_class='form-group mb-3'),
            Field('new_password1', css_class='form-group mb-3'),
            Field('new_password2', css_class='form-group mb-3'),
            Submit('submit', 'Change Password', css_class='btn btn-3d btn-lg w-100')
        )

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError('Your current password is incorrect.')
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError('The two password fields must match.')
            
            if len(new_password1) < 8:
                raise ValidationError('Password must be at least 8 characters long.')

        return cleaned_data

    def save(self):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()
        return self.user
