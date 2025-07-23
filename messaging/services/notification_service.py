from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

User = get_user_model()
logger = logging.getLogger('messaging')
channel_layer = get_channel_layer()

class NotificationService:
    @staticmethod
    def send_new_message_notifications(message):
        """Send notifications for new messages"""
        try:
            # Get recipients (all participants except sender)
            recipients = message.conversation.participants.exclude(id=message.sender.id)
            
            for recipient in recipients:
                # Check notification preferences
                from .models import ConversationSettings
                try:
                    settings_obj = ConversationSettings.objects.get(
                        conversation=message.conversation,
                        user=recipient
                    )
                    if settings_obj.is_muted or not settings_obj.custom_notifications:
                        continue
                except ConversationSettings.DoesNotExist:
                    pass  # Use default notification behavior
                
                # Send WebSocket notification
                NotificationService.send_websocket_notification(
                    recipient,
                    {
                        'type': 'new_message',
                        'message': {
                            'id': str(message.id),
                            'conversation_id': str(message.conversation.id),
                            'conversation_name': str(message.conversation),
                            'sender_name': message.sender.display_name,
                            'sender_avatar': message.sender.profile_picture.url if message.sender.profile_picture else '',
                            'content': message.content[:100],
                            'message_type': message.message_type,
                            'created_at': message.created_at.isoformat()
                        }
                    }
                )
                
                # Send email notification if user is offline
                if NotificationService.should_send_email_notification(recipient, message):
                    NotificationService.send_message_email_notification(recipient, message)
            
            logger.info(f"Sent notifications for message {message.id} to {len(recipients)} recipients")
        
        except Exception as e:
            logger.error(f"Failed to send message notifications: {str(e)}")
    
    @staticmethod
    def send_websocket_notification(user, notification_data):
        """Send real-time notification via WebSocket"""
        try:
            user_group_name = f'user_{user.id}'
            async_to_sync(channel_layer.group_send)(
                user_group_name,
                {
                    'type': 'send_notification',
                    'notification': notification_data
                }
            )
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification to {user.username}: {str(e)}")
    
    @staticmethod
    def should_send_email_notification(user, message):
        """Determine if email notification should be sent"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Don't send email if user was active recently (within 5 minutes)
        recent_activity_threshold = timezone.now() - timedelta(minutes=5)
        if user.last_activity and user.last_activity > recent_activity_threshold:
            return False
        
        # Check if it's a group message and user prefers no group notifications
        if message.conversation.is_group:
            # Could add user preference for group email notifications here
            return False
        
        return True
    
    @staticmethod
    def send_message_email_notification(user, message):
        """Send email notification for new message"""
        try:
            subject = f'New message from {message.sender.display_name}'
            
            if message.conversation.is_group:
                subject = f'New message in {message.conversation.group_name}'
            
            context = {
                'recipient': user,
                'message': message,
                'conversation': message.conversation,
                'sender': message.sender,
                'message_url': f"{settings.SITE_URL}/messages/conversation/{message.conversation.id}/"
            }
            
            html_content = render_to_string('emails/new_message.html', context)
            text_content = strip_tags(html_content)
            
            send_mail(
                subject,
                text_content,
                settings.EMAIL_HOST_USER,
                [user.email],
                html_message=html_content,
                fail_silently=True
            )
            
            logger.info(f"Email notification sent to {user.email} for message {message.id}")
        
        except Exception as e:
            logger.error(f"Failed to send email notification to {user.email}: {str(e)}")
    
    @staticmethod
    def send_conversation_invitation(conversation, invited_user, inviter):
        """Send notification for conversation invitation"""
        try:
            # WebSocket notification
            NotificationService.send_websocket_notification(
                invited_user,
                {
                    'type': 'conversation_invitation',
                    'conversation': {
                        'id': str(conversation.id),
                        'name': str(conversation),
                        'is_group': conversation.is_group,
                        'inviter_name': inviter.display_name,
                        'participant_count': conversation.participants.count()
                    }
                }
            )
            
            # Email notification
            subject = f'{inviter.display_name} added you to a conversation'
            if conversation.is_group:
                subject = f'{inviter.display_name} added you to "{conversation.group_name}"'
            
            context = {
                'invited_user': invited_user,
                'conversation': conversation,
                'inviter': inviter,
                'conversation_url': f"{settings.SITE_URL}/messages/conversation/{conversation.id}/"
            }
            
            html_content = render_to_string('emails/conversation_invitation.html', context)
            text_content = strip_tags(html_content)
            
            send_mail(
                subject,
                text_content,
                settings.EMAIL_HOST_USER,
                [invited_user.email],
                html_message=html_content,
                fail_silently=True
            )
            
            logger.info(f"Conversation invitation sent to {invited_user.email}")
        
        except Exception as e:
            logger.error(f"Failed to send conversation invitation: {str(e)}")
    
    @staticmethod
    def send_bulk_message_notification(conversation, message, exclude_sender=True):
        """Send bulk notifications for group messages"""
        recipients = conversation.participants.all()
        
        if exclude_sender:
            recipients = recipients.exclude(id=message.sender.id)
        
        for recipient in recipients:
            NotificationService.send_websocket_notification(
                recipient,
                {
                    'type': 'bulk_message',
                    'message': {
                        'conversation_id': str(conversation.id),
                        'sender_name': message.sender.display_name,
                        'content_preview': message.content[:50],
                        'created_at': message.created_at.isoformat()
                    }
                }
            )
