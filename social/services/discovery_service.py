from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from ..models import Follow, UserProfile
import logging

User = get_user_model()
logger = logging.getLogger('social')

class DiscoveryService:
    @staticmethod
    def get_recommended_users(user, limit=10):
        """Get recommended users for a user to follow"""
        try:
            # Get users that user's followers also follow (collaborative filtering)
            user_following = Follow.objects.filter(follower=user).values_list('followed_id', flat=True)
            
            # Find users followed by people the user follows
            recommended_from_network = User.objects.filter(
                followers__follower__following__follower=user,
                is_active=True,
                is_email_verified=True
            ).exclude(
                id=user.id
            ).exclude(
                id__in=user_following
            ).annotate(
                mutual_connections=Count('followers__follower__following__follower', 
                                       filter=Q(followers__follower__following__follower=user))
            ).order_by('-mutual_connections')[:limit//2]
            
            # Get users from same college
            college_users = []
            if user.college:
                college_users = User.objects.filter(
                    college=user.college,
                    is_active=True,
                    is_email_verified=True
                ).exclude(
                    id=user.id
                ).exclude(
                    id__in=user_following
                ).exclude(
                    id__in=[u.id for u in recommended_from_network]
                ).order_by('-date_joined')[:limit//4]
            
            # Get popular users (high follower count)
            popular_users = User.objects.annotate(
                followers_count=Count('followers')
            ).filter(
                is_active=True,
                is_email_verified=True,
                followers_count__gt=0
            ).exclude(
                id=user.id
            ).exclude(
                id__in=user_following
            ).exclude(
                id__in=[u.id for u in recommended_from_network] + [u.id for u in college_users]
            ).order_by('-followers_count')[:limit//4]
            
            # Combine recommendations
            recommendations = list(recommended_from_network) + list(college_users) + list(popular_users)
            
            # If still need more, add recent active users
            if len(recommendations) < limit:
                remaining = limit - len(recommendations)
                recent_active = User.objects.filter(
                    is_active=True,
                    is_email_verified=True,
                    last_activity__gte=timezone.now() - timedelta(days=7)
                ).exclude(
                    id=user.id
                ).exclude(
                    id__in=user_following
                ).exclude(
                    id__in=[u.id for u in recommendations]
                ).order_by('-last_activity')[:remaining]
                
                recommendations.extend(recent_active)
            
            logger.info(f"Generated {len(recommendations)} recommendations for user {user.username}")
            return recommendations[:limit]
        
        except Exception as e:
            logger.error(f"Error generating recommendations for user {user.username}: {str(e)}")
            # Fallback to simple recommendation
            return User.objects.filter(
                is_active=True,
                is_email_verified=True
            ).exclude(id=user.id).order_by('?')[:limit]
    
    @staticmethod
    def search_users(query, category=None, exclude_user=None):
        """Search users with optional category filter"""
        users = User.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query),
            is_active=True,
            is_email_verified=True
        )
        
        if exclude_user:
            users = users.exclude(id=exclude_user.id)
        
        # Apply category filters
        if category == 'active':
            week_ago = timezone.now() - timedelta(days=7)
            users = users.filter(last_activity__gte=week_ago).order_by('-last_activity')
        
        elif category == 'popular':
            users = users.annotate(
                followers_count=Count('followers')
            ).order_by('-followers_count')
        
        elif category == 'recent':
            users = users.order_by('-date_joined')
        
        elif category == 'same_college' and exclude_user and exclude_user.college:
            users = users.filter(college=exclude_user.college).order_by('-date_joined')
        
        else:
            users = users.order_by('first_name', 'last_name')
        
        return users
    
    @staticmethod
    def get_mutual_connections(user1, user2):
        """Get mutual connections between two users"""
        user1_following = Follow.objects.filter(follower=user1).values_list('followed_id', flat=True)
        user2_following = Follow.objects.filter(follower=user2).values_list('followed_id', flat=True)
        
        mutual_ids = set(user1_following) & set(user2_following)
        
        return User.objects.filter(id__in=mutual_ids)
    
    @staticmethod
    def get_user_similarity_score(user1, user2):
        """Calculate similarity score between two users based on various factors"""
        score = 0
        
        # Same college
        if user1.college and user2.college and user1.college == user2.college:
            score += 20
        
        # Same year of study
        if user1.year_of_study and user2.year_of_study and user1.year_of_study == user2.year_of_study:
            score += 10
        
        # Quiz performance similarity
        from quiz_app.models import UserQuizAttempt
        user1_categories = set(UserQuizAttempt.objects.filter(
            user=user1
        ).values_list('quiz__category_id', flat=True))
        
        user2_categories = set(UserQuizAttempt.objects.filter(
            user=user2
        ).values_list('quiz__category_id', flat=True))
        
        common_categories = user1_categories & user2_categories
        score += len(common_categories) * 5
        
        # Mutual connections
        mutual_count = DiscoveryService.get_mutual_connections(user1, user2).count()
        score += mutual_count * 3
        
        return score
    
    @staticmethod
    def get_trending_users(days=7, limit=10):
        """Get trending users based on recent follower growth"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        trending_users = User.objects.annotate(
            recent_followers=Count('followers', filter=Q(followers__created_at__gte=cutoff_date)),
            total_followers=Count('followers')
        ).filter(
            is_active=True,
            is_email_verified=True,
            recent_followers__gt=0
        ).order_by('-recent_followers', '-total_followers')[:limit]
        
        return trending_users
    
    @staticmethod
    def get_users_by_activity(activity_type, limit=10):
        """Get users by specific activity type"""
        from ..models import SocialFeed
        
        users = User.objects.filter(
            feed_activities__activity_type=activity_type,
            is_active=True,
            is_email_verified=True
        ).annotate(
            activity_count=Count('feed_activities', filter=Q(feed_activities__activity_type=activity_type))
        ).order_by('-activity_count')[:limit]
        
        return users
