from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import CustomUser
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_verification_email(user_id, otp):
    try:
        user = CustomUser.objects.get(id=user_id)
        
        subject = 'Verify Your Email - Quiz Platform'
        html_message = render_to_string('emails/verification_email.html', {
            'user': user,
            'otp': otp,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            [user.email],
            html_message=html_message,
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except CustomUser.DoesNotExist:
        logger.error(f"User with ID {user_id} does not exist")
        return False
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        return False

@shared_task
def send_weekly_report():
    """Send weekly activity reports to all users"""
    from django.utils import timezone
    from datetime import timedelta
    
    week_ago = timezone.now() - timedelta(days=7)
    users = CustomUser.objects.filter(is_active=True, is_email_verified=True)
    
    for user in users:
        try:
            # Get user's weekly stats
            recent_attempts = user.userquizattempt_set.filter(
                created_at__gte=week_ago
            ).count()
            
            if recent_attempts > 0:  # Only send if user was active
                subject = f'Your Weekly Quiz Report - {recent_attempts} Quizzes Completed!'
                html_message = render_to_string('emails/weekly_report.html', {
                    'user': user,
                    'recent_attempts': recent_attempts,
                    'week_ago': week_ago,
                })
                plain_message = strip_tags(html_message)
                
                send_mail(
                    subject,
                    plain_message,
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    html_message=html_message,
                )
                
                logger.info(f"Weekly report sent to {user.email}")
        
        except Exception as e:
            logger.error(f"Failed to send weekly report to {user.email}: {str(e)}")
    
    return f"Weekly reports sent to active users"
