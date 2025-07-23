from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from celery import shared_task
import logging
import random
import string

logger = logging.getLogger('accounts')

class EmailService:
    @staticmethod
    def generate_otp():
        """Generate 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    def send_verification_email(user, otp):
        """Send email verification OTP"""
        try:
            subject = 'Verify Your Email - Quiz Platform'
            
            context = {
                'user': user,
                'otp': otp,
                'platform_name': 'Quiz Platform',
                'support_email': settings.EMAIL_HOST_USER
            }
            
            html_content = render_to_string('emails/verification_email.html', context)
            text_content = strip_tags(html_content)
            
            msg = EmailMultiAlternatives(
                subject,
                text_content,
                settings.EMAIL_HOST_USER,
                [user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Verification email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email after successful registration"""
        try:
            subject = 'Welcome to Quiz Platform!'
            
            context = {
                'user': user,
                'platform_name': 'Quiz Platform',
                'login_url': f"{settings.SITE_URL}/accounts/login/",
                'dashboard_url': f"{settings.SITE_URL}/accounts/dashboard/"
            }
            
            html_content = render_to_string('emails/welcome_email.html', context)
            text_content = strip_tags(html_content)
            
            msg = EmailMultiAlternatives(
                subject,
                text_content,
                settings.EMAIL_HOST_USER,
                [user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Welcome email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_password_reset_notification(user):
        """Send password reset notification"""
        try:
            subject = 'Password Reset Successful - Quiz Platform'
            
            context = {
                'user': user,
                'platform_name': 'Quiz Platform',
                'login_url': f"{settings.SITE_URL}/accounts/login/",
                'support_email': settings.EMAIL_HOST_USER
            }
            
            html_content = render_to_string('emails/password_reset_notification.html', context)
            text_content = strip_tags(html_content)
            
            msg = EmailMultiAlternatives(
                subject,
                text_content,
                settings.EMAIL_HOST_USER,
                [user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Password reset notification sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset notification to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_quiz_completion_notification(user, quiz_attempt):
        """Send quiz completion notification"""
        try:
            subject = f'Quiz Completed: {quiz_attempt.quiz.title}'
            
            context = {
                'user': user,
                'attempt': quiz_attempt,
                'quiz': quiz_attempt.quiz,
                'platform_name': 'Quiz Platform',
                'results_url': f"{settings.SITE_URL}/quiz/results/{quiz_attempt.id}/"
            }
            
            html_content = render_to_string('emails/quiz_completion.html', context)
            text_content = strip_tags(html_content)
            
            msg = EmailMultiAlternatives(
                subject,
                text_content,
                settings.EMAIL_HOST_USER,
                [user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Quiz completion notification sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send quiz completion notification to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_weekly_report(user):
        """Send weekly activity report"""
        try:
            from quiz_app.models import UserQuizAttempt
            from datetime import timedelta
            from django.utils import timezone
            
            week_ago = timezone.now() - timedelta(days=7)
            
            # Get weekly stats
            weekly_attempts = UserQuizAttempt.objects.filter(
                user=user,
                created_at__gte=week_ago
            )
            
            if weekly_attempts.count() == 0:
                return False  # Don't send report if no activity
            
            completed_attempts = weekly_attempts.filter(status='completed')
            avg_score = completed_attempts.aggregate(avg=models.Avg('score'))['avg'] or 0
            
            subject = f'Your Weekly Quiz Report - {completed_attempts.count()} Quizzes Completed!'
            
            context = {
                'user': user,
                'week_start': week_ago.date(),
                'week_end': timezone.now().date(),
                'total_attempts': weekly_attempts.count(),
                'completed_attempts': completed_attempts.count(),
                'average_score': round(avg_score, 1),
                'platform_name': 'Quiz Platform',
                'dashboard_url': f"{settings.SITE_URL}/accounts/dashboard/"
            }
            
            html_content = render_to_string('emails/weekly_report.html', context)
            text_content = strip_tags(html_content)
            
            msg = EmailMultiAlternatives(
                subject,
                text_content,
                settings.EMAIL_HOST_USER,
                [user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Weekly report sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send weekly report to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_bulk_notification(users, subject, template, context=None):
        """Send bulk notification to multiple users"""
        if context is None:
            context = {}
        
        successful_sends = 0
        
        for user in users:
            try:
                user_context = context.copy()
                user_context['user'] = user
                user_context['platform_name'] = 'Quiz Platform'
                
                html_content = render_to_string(template, user_context)
                text_content = strip_tags(html_content)
                
                msg = EmailMultiAlternatives(
                    subject,
                    text_content,
                    settings.EMAIL_HOST_USER,
                    [user.email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                
                successful_sends += 1
                
            except Exception as e:
                logger.error(f"Failed to send bulk notification to {user.email}: {str(e)}")
        
        logger.info(f"Bulk notification sent to {successful_sends}/{len(users)} users")
        return successful_sends
