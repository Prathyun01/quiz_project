from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class Follow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    followed = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'followed')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"

class SocialNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('follow', 'New Follower'),
        ('unfollow', 'Unfollowed'),
        ('quiz_shared', 'Quiz Shared'),
        ('achievement', 'Achievement Unlocked'),
        ('mention', 'Mentioned'),
        ('quiz_challenge', 'Quiz Challenge'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_notifications', on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional related objects
    related_quiz_id = models.CharField(max_length=100, blank=True)
    related_url = models.URLField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()

class UserProfile(models.Model):
    """Extended user profile for social features"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='social_profile')
    bio_extended = models.TextField(max_length=1000, blank=True, help_text='Extended bio for social profile')
    website_url = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    # Social stats
    posts_count = models.IntegerField(default=0)
    likes_received = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)
    
    # Privacy settings
    show_email = models.BooleanField(default=False)
    show_quiz_history = models.BooleanField(default=True)
    show_followers = models.BooleanField(default=True)
    show_following = models.BooleanField(default=True)
    allow_messages = models.BooleanField(default=True)
    
    # Activity settings
    notify_on_follow = models.BooleanField(default=True)
    notify_on_quiz_share = models.BooleanField(default=True)
    notify_on_mention = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Social Profile"
    
    @property
    def followers_count(self):
        return Follow.objects.filter(followed=self.user).count()
    
    @property
    def following_count(self):
        return Follow.objects.filter(follower=self.user).count()
    
    def is_following(self, user):
        """Check if this user is following another user"""
        return Follow.objects.filter(follower=self.user, followed=user).exists()
    
    def is_followed_by(self, user):
        """Check if this user is followed by another user"""
        return Follow.objects.filter(follower=user, followed=self.user).exists()

class QuizShare(models.Model):
    """Track quiz sharing activities"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_shares')
    quiz_id = models.CharField(max_length=100)  # Quiz UUID as string
    quiz_title = models.CharField(max_length=200)
    shared_with = models.ManyToManyField(User, related_name='received_quiz_shares', blank=True)
    share_message = models.TextField(max_length=500, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} shared {self.quiz_title}"

class Achievement(models.Model):
    """User achievements and badges"""
    ACHIEVEMENT_TYPES = [
        ('quiz_master', 'Quiz Master'),
        ('streak_keeper', 'Streak Keeper'),
        ('social_butterfly', 'Social Butterfly'),
        ('perfectionist', 'Perfectionist'),
        ('speed_demon', 'Speed Demon'),
        ('knowledge_seeker', 'Knowledge Seeker'),
        ('mentor', 'Mentor'),
        ('challenger', 'Challenger'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    icon = models.CharField(max_length=50, default='fas fa-trophy')
    color = models.CharField(max_length=7, default='#FFD700')
    points = models.IntegerField(default=10)
    is_rare = models.BooleanField(default=False)
    requirements = models.JSONField(default=dict, help_text='Achievement requirements in JSON format')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class UserAchievement(models.Model):
    """Track user achievements"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    progress = models.JSONField(default=dict, help_text='Progress tracking data')
    is_displayed = models.BooleanField(default=True, help_text='Show on profile')
    
    class Meta:
        unique_together = ('user', 'achievement')
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"

class SocialFeed(models.Model):
    """Social activity feed"""
    ACTIVITY_TYPES = [
        ('quiz_completed', 'Quiz Completed'),
        ('quiz_shared', 'Quiz Shared'),
        ('achievement_earned', 'Achievement Earned'),
        ('user_followed', 'User Followed'),
        ('quiz_created', 'Quiz Created'),
        ('milestone_reached', 'Milestone Reached'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feed_activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

class UserInteraction(models.Model):
    """Track user interactions (likes, shares, etc.)"""
    INTERACTION_TYPES = [
        ('like', 'Like'),
        ('share', 'Share'),
        ('comment', 'Comment'),
        ('bookmark', 'Bookmark'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    target_type = models.CharField(max_length=50)  # 'quiz', 'achievement', 'post', etc.
    target_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'target_type', 'target_id', 'interaction_type')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type}d {self.target_type} {self.target_id}"
