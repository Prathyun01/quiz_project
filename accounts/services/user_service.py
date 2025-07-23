from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from ..models import UserActivity
import logging

User = get_user_model()
logger = logging.getLogger('accounts')

class UserService:
    @staticmethod
    def get_user_stats(user):
        """Get comprehensive user statistics"""
        from quiz_app.models import UserQuizAttempt
        
        attempts = UserQuizAttempt.objects.filter(user=user)
        completed_attempts = attempts.filter(status='completed')
        
        stats = {
            'total_attempts': attempts.count(),
            'completed_attempts': completed_attempts.count(),
            'average_score': completed_attempts.aggregate(avg=Avg('score'))['avg'] or 0,
            'best_score': completed_attempts.aggregate(max=models.Max('score'))['max'] or 0,
            'total_time_spent': sum([
                attempt.time_taken.total_seconds() for attempt in completed_attempts 
                if attempt.time_taken
            ], timedelta()).total_seconds(),
            'completion_rate': (completed_attempts.count() / max(attempts.count(), 1)) * 100,
        }
        
        # Activity stats
        week_ago = timezone.now() - timedelta(days=7)
        stats['weekly_activity'] = UserActivity.objects.filter(
            user=user,
            timestamp__gte=week_ago
        ).count()
        
        return stats
    
    @staticmethod
    def get_recommended_users(user, limit=10):
        """Get recommended users based on similar interests"""
        from quiz_app.models import UserQuizAttempt
        
        # Get categories user has attempted
        user_categories = UserQuizAttempt.objects.filter(user=user).values_list(
            'quiz__category', flat=True
        ).distinct()
        
        if not user_categories:
            # Return random active users if no quiz history
            return User.objects.filter(
                is_active=True,
                is_email_verified=True
            ).exclude(id=user.id).order_by('?')[:limit]
        
        # Find users who attempted quizzes in similar categories
        similar_users = User.objects.filter(
            userquizattempt__quiz__category__in=user_categories,
            is_active=True,
            is_email_verified=True
        ).exclude(id=user.id).annotate(
            common_categories=Count('userquizattempt__quiz__category', distinct=True)
        ).order_by('-common_categories')[:limit]
        
        return similar_users
    
    @staticmethod
    def search_users(query, exclude_user=None, limit=20):
        """Search users by name, username, or email"""
        users = User.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(email__icontains=query),
            is_active=True,
            is_email_verified=True
        )
        
        if exclude_user:
            users = users.exclude(id=exclude_user.id)
        
        return users.order_by('first_name', 'last_name')[:limit]
    
    @staticmethod
    def update_user_activity(user, action, description="", request=None):
        """Update user activity log"""
        ip_address = None
        user_agent = ""
        
        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        UserActivity.objects.create(
            user=user,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"User activity logged: {user.username} - {action}")
    
    @staticmethod
    def get_user_activity_timeline(user, days=30):
        """Get user activity timeline"""
        cutoff_date = timezone.now() - timedelta(days=days)
        activities = UserActivity.objects.filter(
            user=user,
            timestamp__gte=cutoff_date
        ).order_by('-timestamp')
        
        return activities
    
    @staticmethod
    def check_username_availability(username, exclude_user=None):
        """Check if username is available"""
        users = User.objects.filter(username=username)
        if exclude_user:
            users = users.exclude(id=exclude_user.id)
        return not users.exists()
    
    @staticmethod
    def generate_unique_username(base_username):
        """Generate a unique username based on a base"""
        if UserService.check_username_availability(base_username):
            return base_username
        
        counter = 1
        while True:
            new_username = f"{base_username}_{counter}"
            if UserService.check_username_availability(new_username):
                return new_username
            counter += 1
    
    @staticmethod
    def get_active_users_count():
        """Get count of active users"""
        return User.objects.filter(
            is_active=True,
            is_email_verified=True
        ).count()
    
    @staticmethod
    def get_recent_registrations(days=7):
        """Get recent user registrations"""
        cutoff_date = timezone.now() - timedelta(days=days)
        return User.objects.filter(
            date_joined__gte=cutoff_date
        ).order_by('-date_joined')
