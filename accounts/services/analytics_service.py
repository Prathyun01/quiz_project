from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta, date
from collections import defaultdict
import logging

User = get_user_model()
logger = logging.getLogger('accounts')

class AnalyticsService:
    @staticmethod
    def get_user_registration_stats(days=30):
        """Get user registration statistics"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        registrations = User.objects.filter(
            date_joined__gte=start_date,
            date_joined__lte=end_date
        ).extra(
            select={'day': 'date(date_joined)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        # Fill in missing days with 0
        registration_data = defaultdict(int)
        for reg in registrations:
            registration_data[reg['day']] = reg['count']
        
        # Generate complete date range
        current_date = start_date.date()
        daily_stats = []
        
        while current_date <= end_date.date():
            daily_stats.append({
                'date': current_date,
                'count': registration_data.get(current_date, 0)
            })
            current_date += timedelta(days=1)
        
        return {
            'daily_registrations': daily_stats,
            'total_new_users': sum(stat['count'] for stat in daily_stats),
            'average_daily_registrations': sum(stat['count'] for stat in daily_stats) / len(daily_stats)
        }
    
    @staticmethod
    def get_user_engagement_stats():
        """Get user engagement statistics"""
        total_users = User.objects.count()
        verified_users = User.objects.filter(is_email_verified=True).count()
        active_users = User.objects.filter(is_active=True).count()
        
        # Users active in last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        weekly_active = User.objects.filter(last_activity__gte=week_ago).count()
        
        # Users active in last 30 days
        month_ago = timezone.now() - timedelta(days=30)
        monthly_active = User.objects.filter(last_activity__gte=month_ago).count()
        
        return {
            'total_users': total_users,
            'verified_users': verified_users,
            'active_users': active_users,
            'weekly_active_users': weekly_active,
            'monthly_active_users': monthly_active,
            'verification_rate': (verified_users / max(total_users, 1)) * 100,
            'weekly_engagement_rate': (weekly_active / max(verified_users, 1)) * 100,
            'monthly_engagement_rate': (monthly_active / max(verified_users, 1)) * 100
        }
    
    @staticmethod
    def get_college_distribution():
        """Get distribution of users by college"""
        from accounts.models import College
        
        college_stats = College.objects.annotate(
            user_count=Count('customuser')
        ).order_by('-user_count')
        
        return college_stats
    
    @staticmethod
    def get_user_activity_heatmap(days=30):
        """Get user activity heatmap data"""
        from accounts.models import UserActivity
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        activities = UserActivity.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).extra(
            select={
                'hour': 'extract(hour from timestamp)',
                'day_of_week': 'extract(dow from timestamp)'
            }
        ).values('hour', 'day_of_week').annotate(count=Count('id'))
        
        # Initialize heatmap data
        heatmap_data = {}
        for day in range(7):  # 0 = Sunday, 6 = Saturday
            heatmap_data[day] = {}
            for hour in range(24):
                heatmap_data[day][hour] = 0
        
        # Fill in actual data
        for activity in activities:
            day = int(activity['day_of_week'])
            hour = int(activity['hour'])
            heatmap_data[day][hour] = activity['count']
        
        return heatmap_data
    
    @staticmethod
    def get_top_performers(limit=10):
        """Get top performing users based on quiz scores"""
        from quiz_app.models import UserQuizAttempt
        
        top_users = User.objects.annotate(
            total_score=models.Sum('userquizattempt__score', filter=Q(userquizattempt__status='completed')),
            total_attempts=Count('userquizattempt', filter=Q(userquizattempt__status='completed')),
            avg_score=Avg('userquizattempt__score', filter=Q(userquizattempt__status='completed'))
        ).filter(
            total_attempts__gt=0
        ).order_by('-total_score')[:limit]
        
        return top_users
    
    @staticmethod
    def get_user_retention_stats():
        """Calculate user retention statistics"""
        now = timezone.now()
        
        # Cohort analysis by registration month
        retention_data = []
        
        for months_ago in range(12, 0, -1):
            cohort_start = now - timedelta(days=30 * months_ago)
            cohort_end = now - timedelta(days=30 * (months_ago - 1))
            
            # Users who registered in this cohort
            cohort_users = User.objects.filter(
                date_joined__gte=cohort_start,
                date_joined__lt=cohort_end
            )
            
            if cohort_users.count() == 0:
                continue
            
            # Calculate retention for different periods
            week1_active = cohort_users.filter(
                last_activity__gte=cohort_start + timedelta(days=7)
            ).count()
            
            month1_active = cohort_users.filter(
                last_activity__gte=cohort_end
            ).count()
            
            retention_data.append({
                'cohort_month': cohort_start.strftime('%Y-%m'),
                'total_users': cohort_users.count(),
                'week1_retention': (week1_active / cohort_users.count()) * 100,
                'month1_retention': (month1_active / cohort_users.count()) * 100
            })
        
        return retention_data
    
    @staticmethod
    def get_quiz_performance_by_user_segment():
        """Analyze quiz performance by user segments"""
        from quiz_app.models import UserQuizAttempt
        
        segments = {
            'new_users': User.objects.filter(date_joined__gte=timezone.now() - timedelta(days=30)),
            'regular_users': User.objects.filter(
                date_joined__lt=timezone.now() - timedelta(days=30),
                last_activity__gte=timezone.now() - timedelta(days=7)
            ),
            'inactive_users': User.objects.filter(
                last_activity__lt=timezone.now() - timedelta(days=30)
            )
        }
        
        segment_stats = {}
        
        for segment_name, users in segments.items():
            attempts = UserQuizAttempt.objects.filter(
                user__in=users,
                status='completed'
            )
            
            segment_stats[segment_name] = {
                'user_count': users.count(),
                'total_attempts': attempts.count(),
                'avg_score': attempts.aggregate(avg=Avg('score'))['avg'] or 0,
                'completion_rate': (attempts.count() / max(users.count(), 1)) * 100
            }
        
        return segment_stats
