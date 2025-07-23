from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, College, EmailVerificationOTP, UserActivity

@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'location', 'established_year', 'created_at']
    list_filter = ['location', 'established_year']
    search_fields = ['name', 'code', 'location']
    readonly_fields = ['created_at']

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = [
        'email', 'username', 'first_name', 'last_name', 
        'college', 'year_of_study', 'is_email_verified', 
        'total_quiz_attempts', 'average_quiz_score',
        'is_active', 'date_joined'
    ]
    list_filter = [
        'is_active', 'is_staff', 'is_superuser', 
        'is_email_verified', 'year_of_study', 'college'
    ]
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Academic Information', {
            'fields': ('college', 'year_of_study', 'phone_number')
        }),
        ('Profile Information', {
            'fields': ('profile_picture', 'cover_photo', 'bio', 'date_of_birth')
        }),
        ('Social Media', {
            'fields': ('twitter_url', 'linkedin_url', 'github_url')
        }),
        ('Quiz Statistics', {
            'fields': ('total_quiz_attempts', 'total_quiz_score'),
            'classes': ['collapse']
        }),
        ('Account Status', {
            'fields': ('is_email_verified', 'is_private', 'last_activity')
        }),
    )
    
    readonly_fields = ['last_activity']
    
    def average_quiz_score(self, obj):
        return obj.average_quiz_score
    average_quiz_score.short_description = 'Average Score'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['email']
        return self.readonly_fields

@admin.register(EmailVerificationOTP)
class EmailVerificationOTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp', 'created_at', 'is_used', 'is_valid_display']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email', 'user__username', 'otp']
    readonly_fields = ['created_at', 'is_valid_display']
    
    def is_valid_display(self, obj):
        if obj.is_valid:
            return format_html('<span style="color: green;">✓ Valid</span>')
        else:
            return format_html('<span style="color: red;">✗ Invalid/Expired</span>')
    is_valid_display.short_description = 'Status'

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__email', 'user__username', 'description']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False  # Prevent manual addition of activities
