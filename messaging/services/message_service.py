from django.contrib.auth import get_user_model
from django.utils import timezone
from ..models import Message, MessageStatus, Conversation
import logging

User = get_user_model()
logger = logging.getLogger('messaging')

class MessageService:
    @staticmethod
    def create_message_statuses(message, recipients):
        """Create message status records for recipients"""
        status_objects = []
        
        for recipient in recipients:
            status = MessageStatus(
                message=message,
                recipient=recipient,
                is_delivered=True,  # Assume immediate delivery for web app
                delivered_at=timezone.now()
            )
            status_objects.append(status)
        
        MessageStatus.objects.bulk_create(status_objects)
        logger.info(f"Created message statuses for {len(status_objects)} recipients")
    
    @staticmethod
    def get_or_create_direct_conversation(user1, user2):
        """Get or create a direct conversation between two users"""
        # Check if conversation already exists
        conversation = Conversation.objects.filter(
            is_group=False,
            participants=user1
        ).filter(participants=user2).first()
        
        if conversation:
            return conversation, False
        
        # Create new conversation
        conversation = Conversation.objects.create(is_group=False)
        conversation.participants.add(user1, user2)
        
        logger.info(f"Created new conversation between {user1.username} and {user2.username}")
        return conversation, True
    
    @staticmethod
    def send_message(sender, conversation, content, message_type='text', attachment=None, reply_to=None):
        """Send a message in a conversation"""
        try:
            # Create message
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                content=content,
                message_type=message_type,
                attachment=attachment,
                reply_to=reply_to
            )
            
            # Create message statuses for other participants
            recipients = conversation.participants.exclude(id=sender.id)
            MessageService.create_message_statuses(message, recipients)
            
            # Update conversation timestamp
            conversation.updated_at = timezone.now()
            conversation.save()
            
            logger.info(f"Message sent by {sender.username} in conversation {conversation.id}")
            return message
        
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            raise
    
    @staticmethod
    def get_unread_count(user):
        """Get total unread message count for a user"""
        return MessageStatus.objects.filter(
            recipient=user,
            is_read=False
        ).count()
    
    @staticmethod
    def get_conversation_unread_count(conversation, user):
        """Get unread message count for a specific conversation"""
        return MessageStatus.objects.filter(
            message__conversation=conversation,
            recipient=user,
            is_read=False
        ).count()
    
    @staticmethod
    def mark_conversation_as_read(conversation, user):
        """Mark all messages in a conversation as read for a user"""
        MessageStatus.objects.filter(
            message__conversation=conversation,
            recipient=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        logger.info(f"Marked conversation {conversation.id} as read for {user.username}")
    
    @staticmethod
    def delete_message(message, user):
        """Soft delete a message (only by sender)"""
        if message.sender != user:
            raise PermissionError("Only message sender can delete the message")
        
        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.content = ''  # Clear content for privacy
        message.save()
        
        logger.info(f"Message {message.id} deleted by {user.username}")
    
    @staticmethod
    def search_messages(user, query, conversation=None, message_type=None):
        """Search messages for a user"""
        messages = Message.objects.filter(
            conversation__participants=user,
            is_deleted=False,
            content__icontains=query
        ).select_related('conversation', 'sender')
        
        if conversation:
            messages = messages.filter(conversation=conversation)
        
        if message_type:
            messages = messages.filter(message_type=message_type)
        
        return messages.order_by('-created_at')
    
    @staticmethod
    def get_conversation_analytics(conversation):
        """Get analytics data for a conversation"""
        messages = Message.objects.filter(conversation=conversation, is_deleted=False)
        
        analytics = {
            'total_messages': messages.count(),
            'message_types': {},
            'most_active_user': None,
            'messages_per_day': [],
        }
        
        # Message type breakdown
        for msg_type, _ in Message.MESSAGE_TYPES:
            count = messages.filter(message_type=msg_type).count()
            analytics['message_types'][msg_type] = count
        
        # Most active user
        from django.db.models import Count
        most_active = messages.values('sender__username', 'sender__first_name', 'sender__last_name').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        if most_active:
            analytics['most_active_user'] = {
                'username': most_active['sender__username'],
                'name': f"{most_active['sender__first_name']} {most_active['sender__last_name']}".strip(),
                'message_count': most_active['count']
            }
        
        return analytics
    
    @staticmethod
    def export_conversation(conversation, user, format='json'):
        """Export conversation messages"""
        if not conversation.participants.filter(id=user.id).exists():
            raise PermissionError("User is not a participant in this conversation")
        
        messages = Message.objects.filter(
            conversation=conversation,
            is_deleted=False
        ).select_related('sender').order_by('created_at')
        
        if format == 'json':
            import json
            export_data = {
                'conversation_id': str(conversation.id),
                'conversation_name': str(conversation),
                'exported_by': user.username,
                'exported_at': timezone.now().isoformat(),
                'messages': []
            }
            
            for message in messages:
                export_data['messages'].append({
                    'id': str(message.id),
                    'sender': message.sender.display_name,
                    'content': message.content,
                    'message_type': message.message_type,
                    'created_at': message.created_at.isoformat(),
                    'is_edited': message.is_edited,
                    'edited_at': message.edited_at.isoformat() if message.edited_at else None,
                })
            
            return json.dumps(export_data, indent=2)
        
        elif format == 'txt':
            lines = [
                f"Conversation: {conversation}",
                f"Exported by: {user.display_name}",
                f"Exported at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "=" * 50,
                ""
            ]
            
            for message in messages:
                timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                lines.append(f"[{timestamp}] {message.sender.display_name}: {message.content}")
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
