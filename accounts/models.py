from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid

class College(models.Model):
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=10, unique=True)
    location = models.CharField(max_length=100)  # This matches your admin
    established_year = models.IntegerField(null=True, blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    YEAR_CHOICES = [
        ('1', 'First Year'),
        ('2', 'Second Year'),
        ('3', 'Third Year'),
        ('4', 'Fourth Year'),
        ('5', 'Fifth Year'),
        ('graduate', 'Graduate'),
        ('postgraduate', 'Post Graduate'),
    ]
    
    # Basic Information
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Profile Images
    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.png')
    cover_photo = models.ImageField(upload_to='cover_photos/', blank=True, null=True)
    
    # Academic Information
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True)
    year_of_study = models.CharField(max_length=12, choices=YEAR_CHOICES, blank=True)
    student_id = models.CharField(max_length=50, blank=True)
    
    # Social Media Links
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    
    # Account verification and status
    is_email_verified = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    
    # Activity tracking
    last_activity = models.DateTimeField(null=True, blank=True)
    total_quiz_attempts = models.IntegerField(default=0)
    total_quiz_score = models.IntegerField(default=0)
    
    # Social features
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    
    # Settings
    is_profile_public = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.email
    
    @property
    def display_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def average_quiz_score(self):
        if self.total_quiz_attempts > 0:
            return round(self.total_quiz_score / self.total_quiz_attempts, 2)
        return 0
    
    def update_last_activity(self):
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])

class EmailVerificationOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Verification OTP'
        verbose_name_plural = 'Email Verification OTPs'
    
    def __str__(self):
        return f"OTP for {self.user.email}"
    
    @property
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    
    def is_expired(self):
        return timezone.now() > self.expires_at

# Keep the old EmailVerification model for backward compatibility if needed
class EmailVerification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"OTP for {self.user.email}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at

class UserActivity(models.Model):
    ACTION_CHOICES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('quiz_started', 'Quiz Started'),
        ('quiz_completed', 'Quiz Completed'),
        ('profile_updated', 'Profile Updated'),
        ('message_sent', 'Message Sent'),
        ('document_downloaded', 'Document Downloaded'),
        ('user_followed', 'User Followed'),
        ('chatbot_used', 'Chatbot Used'),
        ('email_verified', 'Email Verified'),
        ('password_changed', 'Password Changed'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()}"
    
    def get_action_icon(self):
        icon_map = {
            'login': 'sign-in-alt',
            'logout': 'sign-out-alt',
            'quiz_started': 'play',
            'quiz_completed': 'check-circle',
            'profile_updated': 'user-edit',
            'message_sent': 'paper-plane',
            'document_downloaded': 'download',
            'user_followed': 'user-plus',
            'chatbot_used': 'robot',
            'email_verified': 'check-circle',
            'password_changed': 'key',
        }
        return icon_map.get(self.action, 'circle')
