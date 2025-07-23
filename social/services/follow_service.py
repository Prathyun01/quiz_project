from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from ..models import Follow, SocialNotification, SocialFeed
import logging

User = get_user_model()
logger = logging.getLogger('social')

class FollowService:
    @staticmethod
    def follow_user(follower, followed):
        """Follow a user and handle all related actions"""
        if follower == followed:
            raise ValueError("Users cannot follow themselves")
        
        try:
            follow_obj, created = Follow.objects.get_or_create(
                follower=follower,
                followed=followed
            )
            
            if created:
                # Send notification
                FollowService.send_follow_notification(follower, followed)
                
                # Create feed activity
                SocialFeed.objects.create(
                    user=follower,
                    activity_type='user_followed',
                    title=f'Started following {followed.display_name}',
                    description=f'{follower.display_name} is now following {followed.display_name}',
                    metadata={'followed_user_id': str(followed.id)},
                    is_public=True
                )
                
                logger.info(f"{follower.username} started following {followed.username}")
                return follow_obj, True
            else:
                logger.info(f"{follower.username} already follows {followed.username}")
                return follow_obj, False
        
        except Exception as e:
            logger.error(f"Error following user: {str(e)}")
            raise
    
    @staticmethod
    def unfollow_user(follower, followed):
        """Unfollow a user"""
        try:
            deleted_count, _ = Follow.objects.filter(
                follower=follower,
                followed=followed
            ).delete()
            
            if deleted_count > 0:
                # Send unfollow notification (optional)
                FollowService.send_unfollow_notification(follower, followed)
                
                logger.info(f"{follower.username} unfollowed {followed.username}")
                return True
            else:
                logger.info(f"{follower.username} was not following {followed.username}")
                return False
        
        except Exception as e:
            logger.error(f"Error unfollowing user: {str(e)}")
            raise
    
    @staticmethod
    def send_follow_notification(follower, followed):
        """Send notification when someone follows a user"""
        try:
            # Check user's notification preferences
            from ..models import UserProfile
            try:
                profile = UserProfile.objects.get(user=followed)
                if not profile.notify_on_follow:
                    return
            except UserProfile.DoesNotExist:
                pass  # Use default behavior
            
            # Create notification
            notification = SocialNotification.objects.create(
                recipient=followed,
                sender=follower,
                notification_type='follow',
                title=f'{follower.display_name} started following you',
                message=f'{follower.display_name} (@{follower.username}) is now following you. Check out their profile!',
                related_url=f'/social/profile/{follower.username}/'
            )
            
            # Send email notification if user prefers it
            FollowService.send_follow_email(follower, followed)
            
            logger.info(f"Follow notification sent to {followed.username}")
        
        except Exception as e:
            logger.error(f"Error sending follow notification: {str(e)}")
    
    @staticmethod
    def send_unfollow_notification(follower, followed):
        """Send notification when someone unfollows (optional)"""
        try:
            # Only send if user wants unfollow notifications
            from ..models import UserProfile
            try:
                profile = UserProfile.objects.get(user=followed)
                if not profile.notify_on_follow:  # Using same setting for unfollow
                    return
            except UserProfile.DoesNotExist:
                return
            
            SocialNotification.objects.create(
                recipient=followed,
                sender=follower,
                notification_type='unfollow',
                title=f'{follower.display_name} unfollowed you',
                message=f'{follower.display_name} (@{follower.username}) is no longer following you.',
                related_url=f'/social/profile/{follower.username}/'
            )
            
            logger.info(f"Unfollow notification sent to {followed.username}")
        
        except Exception as e:
            logger.error(f"Error sending unfollow notification: {str(e)}")
    
    @staticmethod
    def send_follow_email(follower, followed):
        """Send email notification for new follower"""
        try:
            subject = f'{follower.display_name} is now following you!'
            
            context = {
                'followed_user': followed,
                'follower': follower,
                'profile_url': f"{settings.SITE_URL}/social/profile/{follower.username}/",
                'social_dashboard_url': f"{settings.SITE_URL}/social/"
            }
            
            html_content = render_to_string('emails/new_follower.html', context)
            text_content = strip_tags(html_content)
            
            send_mail(
                subject,
                text_content,
                settings.EMAIL_HOST_USER,
                [followed.email],
                html_message=html_content,
                fail_silently=True
            )
            
            logger.info(f"Follow email sent to {followed.email}")
        
        except Exception as e:
            logger.error(f"Error sending follow email: {str(e)}")
    
    @staticmethod
    def get_follow_suggestions(user, limit=5):
        """Get follow suggestions based on user's network"""
        # Get users that user's followers also follow
        following_ids = Follow.objects.filter(follower=user).values_list('followed_id', flat=True)
        
        suggested_users = User.objects.filter(
            followers__follower__following__follower=user,
            is_active=True,
            is_email_verified=True
        ).exclude(
            id=user.id
        ).exclude(
            id__in=following_ids
        ).annotate(
            mutual_connections=Count('followers__follower__following__follower')
        ).order_by('-mutual_connections')[:limit]
        
        return suggested_users
    
    @staticmethod
    def get_follow_stats(user):
        """Get comprehensive follow statistics for a user"""
        followers = Follow.objects.filter(followed=user)
        following = Follow.objects.filter(follower=user)
        
        stats = {
            'followers_count': followers.count(),
            'following_count': following.count(),
            'recent_followers': followers.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'mutual_connections': 0,
            'follower_growth': []
        }
        
        # Calculate follower growth over time
        from django.utils import timezone
        from datetime import timedelta
        
        for days_ago in [30, 60, 90]:
            date_threshold = timezone.now() - timedelta(days=days_ago)
            count = followers.filter(created_at__gte=date_threshold).count()
            stats['follower_growth'].append({
                'days_ago': days_ago,
                'count': count
            })
        
        return stats
    
    @staticmethod
    def bulk_follow_notification(followers_list, followed_user):
        """Send bulk notifications for multiple followers"""
        notifications = []
        
        for follower in followers_list:
            notification = SocialNotification(
                recipient=followed_user,
                sender=follower,
                notification_type='follow',
                title=f'{follower.display_name} started following you',
                message=f'{follower.display_name} (@{follower.username}) is now following you.',
                related_url=f'/social/profile/{follower.username}/'
            )
            notifications.append(notification)
        
        # Bulk create notifications
        SocialNotification.objects.bulk_create(notifications)
        
        logger.info(f"Bulk follow notifications sent for {len(followers_list)} followers to {followed_user.username}")
