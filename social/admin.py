from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import (
    Follow, SocialNotification, UserProfile, QuizShare, 
    Achievement, UserAchievement, SocialFeed, UserInteraction
)

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'followed', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'followed__username']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation

@admin.register(SocialNotification)
class SocialNotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'sender', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'sender__username', 'title']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'followers_count_display', 'following_count_display', 
        'posts_count', 'likes_received', 'created_at'
    ]
    list_filter = ['show_email', 'show_quiz_history', 'created_at']
    search_fields = ['user__username', 'user__email', 'bio_extended']
    readonly_fields = ['created_at', 'updated_at', 'followers_count_display', 'following_count_display']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Profile Information', {
            'fields': ('bio_extended', 'website_url', 'location')
        }),
        ('Social Stats', {
            'fields': ('posts_count', 'likes_received', 'shares_count', 'followers_count_display', 'following_count_display')
        }),
        ('Privacy Settings', {
            'fields': ('show_email', 'show_quiz_history', 'show_followers', 'show_following', 'allow_messages')
        }),
        ('Notification Settings', {
            'fields': ('notify_on_follow', 'notify_on_quiz_share', 'notify_on_mention')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def followers_count_display(self, obj):
        return obj.followers_count
    followers_count_display.short_description = 'Followers'
    
    def following_count_display(self, obj):
        return obj.following_count
    following_count_display.short_description = 'Following'

@admin.register(QuizShare)
class QuizShareAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz_title', 'shared_count', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['user__username', 'quiz_title', 'share_message']
    readonly_fields = ['created_at', 'shared_count']
    
    def shared_count(self, obj):
        return obj.shared_with.count()
    shared_count.short_description = 'Shared With'

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'achievement_type', 'points', 'is_rare', 'earned_count', 'created_at']
    list_filter = ['achievement_type', 'is_rare', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'earned_count']
    
    def earned_count(self, obj):
        return UserAchievement.objects.filter(achievement=obj).count()
    earned_count.short_description = 'Times Earned'

@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'earned_at', 'is_displayed']
    list_filter = ['achievement__achievement_type', 'is_displayed', 'earned_at']
    search_fields = ['user__username', 'achievement__name']
    readonly_fields = ['earned_at']

@admin.register(SocialFeed)
class SocialFeedAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'title', 'is_public', 'created_at']
    list_filter = ['activity_type', 'is_public', 'created_at']
    search_fields = ['user__username', 'title', 'description']
    readonly_fields = ['created_at']

@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'target_user', 'interaction_type', 'target_type', 'created_at']
    list_filter = ['interaction_type', 'target_type', 'created_at']
    search_fields = ['user__username', 'target_user__username']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False
