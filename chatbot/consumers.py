import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatSession, BotMessage
from .services.ai_chat_service import AIChatService
from django.utils import timezone
import asyncio

User = get_user_model()

# Simple in-memory rate limiting for WebSocket
WEBSOCKET_RATE_LIMITS = {}

def check_websocket_rate_limit(user_id, limit=10, window=60):
    """Simple in-memory rate limiting for WebSocket"""
    current_time = timezone.now().timestamp()
    key = f"ws_rate_limit_{user_id}"
    
    if key not in WEBSOCKET_RATE_LIMITS:
        WEBSOCKET_RATE_LIMITS[key] = []
    
    # Clean old entries
    WEBSOCKET_RATE_LIMITS[key] = [
        timestamp for timestamp in WEBSOCKET_RATE_LIMITS[key] 
        if current_time - timestamp < window
    ]
    
    if len(WEBSOCKET_RATE_LIMITS[key]) >= limit:
        return False
    
    WEBSOCKET_RATE_LIMITS[key].append(current_time)
    return True

class ChatbotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        self.chat_group_name = f'chatbot_{self.user.id}'

        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave chat group
        await self.channel_layer.group_discard(
            self.chat_group_name,
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
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON data'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))

    async def handle_chat_message(self, data):
        session_id = self.session_id
        user_message = data.get('message', '').strip()
        provider = data.get('provider', 'perplexity')

        if not user_message:
            return

        # Check rate limiting
        if not check_websocket_rate_limit(self.user.id, limit=10, window=60):
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Rate limit exceeded. Please wait a moment before sending another message.'
            }))
            return

        # Save user message and get bot response
        response_data = await self.process_chat_message(session_id, user_message, provider)
        
        if response_data:
            # Send response back to user
            await self.send(text_data=json.dumps({
                'type': 'chat_response',
                'user_message': response_data['user_message'],
                'bot_response': response_data['bot_response']
            }))

    async def handle_typing(self, data):
        is_typing = data.get('is_typing', False)
        
        # Echo typing indicator
        await self.send(text_data=json.dumps({
            'type': 'typing_indicator',
            'is_typing': is_typing
        }))

    @database_sync_to_async
    def process_chat_message(self, session_id, user_message, provider='perplexity'):
        try:
            # Get session
            session = ChatSession.objects.get(id=session_id, user=self.user)

            # Save user message
            user_msg = BotMessage.objects.create(
                session=session,
                message_type='user',
                content=user_message
            )

            # Get bot response
            ai_service = AIChatService()
            bot_response, response_data = ai_service.get_chat_response(
                user_message=user_message,
                session=session,
                user=self.user,
                provider=provider
            )

            # Save bot response
            bot_msg = BotMessage.objects.create(
                session=session,
                message_type='bot',
                content=bot_response,
                ai_provider=response_data.get('provider', provider),
                response_time=response_data.get('response_time'),
                tokens_used=response_data.get('tokens_used')
            )

            # Update session
            session.updated_at = timezone.now()
            if not session.title or session.title == "New Chat Session":
                session.title = user_message[:50] + ('...' if len(user_message) > 50 else '')
            session.save()

            return {
                'user_message': {
                    'id': str(user_msg.id),
                    'content': user_msg.content,
                    'created_at': user_msg.created_at.isoformat()
                },
                'bot_response': {
                    'id': str(bot_msg.id),
                    'content': bot_msg.content,
                    'created_at': bot_msg.created_at.isoformat(),
                    'response_time': bot_msg.response_time,
                    'model': response_data.get('provider', provider),
                    'processing_time': response_data.get('response_time')
                }
            }

        except Exception as e:
            print(f"Error processing chat message: {e}")
            return None
