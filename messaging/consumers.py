import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation, Message, MessageStatus
from .services.message_service import MessageService
import uuid

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope["user"]
        
        # Check if user is part of conversation
        if await self.is_participant():
            # Join conversation group
            await self.channel_layer.group_add(
                self.conversation_group_name,
                self.channel_name
            )
            await self.accept()
            
            # Send user online status
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'user_status',
                    'user_id': str(self.user.id),
                    'username': self.user.display_name,
                    'status': 'online'
                }
            )
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'conversation_group_name'):
            # Send user offline status
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'user_status',
                    'user_id': str(self.user.id),
                    'username': self.user.display_name,
                    'status': 'offline'
                }
            )
            
            # Leave conversation group
            await self.channel_layer.group_discard(
                self.conversation_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'mark_as_read':
                await self.handle_mark_as_read(data)
            elif message_type == 'message_reaction':
                await self.handle_message_reaction(data)
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON data'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))
    
    async def handle_chat_message(self, data):
        content = data.get('content', '').strip()
        reply_to_id = data.get('reply_to_id')
        
        if not content:
            return
        
        # Save message to database
        message = await self.save_message(content, reply_to_id)
        
        if message:
            # Send message to conversation group
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': str(message.id),
                        'content': message.content,
                        'sender_id': str(message.sender.id),
                        'sender_name': message.sender.display_name,
                        'sender_avatar': message.sender.profile_picture.url if message.sender.profile_picture else '',
                        'created_at': message.created_at.isoformat(),
                        'message_type': message.message_type,
                        'reply_to': {
                            'id': str(message.reply_to.id),
                            'content': message.reply_to.content[:100],
                            'sender_name': message.reply_to.sender.display_name
                        } if message.reply_to else None
                    }
                }
            )
    
    async def handle_typing(self, data):
        is_typing = data.get('is_typing', False)
        
        # Send typing indicator to conversation group (except sender)
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'typing_indicator',
                'user_id': str(self.user.id),
                'username': self.user.display_name,
                'is_typing': is_typing,
                'sender_channel': self.channel_name  # Exclude sender
            }
        )
    
    async def handle_mark_as_read(self, data):
        await self.mark_messages_as_read()
        
        # Notify other users that messages were read
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'messages_read',
                'user_id': str(self.user.id),
                'username': self.user.display_name,
                'sender_channel': self.channel_name
            }
        )
    
    async def handle_message_reaction(self, data):
        message_id = data.get('message_id')
        reaction_type = data.get('reaction_type')
        
        reaction_data = await self.toggle_message_reaction(message_id, reaction_type)
        
        if reaction_data:
            # Send reaction update to conversation group
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'message_reaction',
                    'message_id': message_id,
                    'user_id': str(self.user.id),
                    'username': self.user.display_name,
                    'reaction_type': reaction_type,
                    'action': reaction_data['action'],
                    'reaction_counts': reaction_data['reaction_counts']
                }
            )
    
    # WebSocket message handlers
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def user_status(self, event):
        # Don't send status update to the user themselves
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps(event))
    
    async def typing_indicator(self, event):
        # Don't send typing indicator to the typing user
        if event.get('sender_channel') != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
    
    async def messages_read(self, event):
        # Don't send read status to the reader themselves
        if event.get('sender_channel') != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'messages_read',
                'user_id': event['user_id'],
                'username': event['username']
            }))
    
    async def message_reaction(self, event):
        await self.send(text_data=json.dumps(event))
    
    # Database operations
    @database_sync_to_async
    def is_participant(self):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return conversation.participants.filter(id=self.user.id).exists()
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content, reply_to_id=None):
        try:
            conversation = Conversation.objects.get(
                id=self.conversation_id,
                participants=self.user
            )
            
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=content
            )
            
            # Handle reply
            if reply_to_id:
                try:
                    reply_to = Message.objects.get(
                        id=reply_to_id,
                        conversation=conversation
                    )
                    message.reply_to = reply_to
                    message.save()
                except Message.DoesNotExist:
                    pass
            
            # Create message statuses for other participants
            participants = conversation.participants.exclude(id=self.user.id)
            MessageService.create_message_statuses(message, participants)
            
            # Update conversation timestamp
            conversation.updated_at = timezone.now()
            conversation.save()
            
            return message
        
        except Exception as e:
            print(f"Error saving message: {e}")
            return None
    
    @database_sync_to_async
    def mark_messages_as_read(self):
        try:
            conversation = Conversation.objects.get(
                id=self.conversation_id,
                participants=self.user
            )
            conversation.mark_as_read(self.user)
            return True
        except Exception as e:
            print(f"Error marking messages as read: {e}")
            return False
    
    @database_sync_to_async
    def toggle_message_reaction(self, message_id, reaction_type):
        try:
            from .models import MessageReaction
            from django.db.models import Count
            
            message = Message.objects.get(
                id=message_id,
                conversation__participants=self.user
            )
            
            # Toggle reaction
            reaction, created = MessageReaction.objects.get_or_create(
                message=message,
                user=self.user,
                defaults={'reaction_type': reaction_type}
            )
            
            if not created:
                if reaction.reaction_type == reaction_type:
                    reaction.delete()
                    action = 'removed'
                else:
                    reaction.reaction_type = reaction_type
                    reaction.save()
                    action = 'updated'
            else:
                action = 'added'
            
            # Get updated reaction counts
            reactions = MessageReaction.objects.filter(message=message).values(
                'reaction_type'
            ).annotate(count=Count('id'))
            
            reaction_counts = {r['reaction_type']: r['count'] for r in reactions}
            
            return {
                'action': action,
                'reaction_counts': reaction_counts
            }
        
        except Exception as e:
            print(f"Error toggling reaction: {e}")
            return None
