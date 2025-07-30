import requests
import json
import time
import logging
import hashlib
from django.conf import settings
from django.utils import timezone

# Import other AI providers
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger('chatbot')

# Simple in-memory cache for AI responses (per server instance)
AI_RESPONSE_CACHE = {}

class AIChatService:
    def __init__(self):
        print("Initializing AIChatService...")
        
        # OpenAI configuration
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY and OpenAI:
            print(f"OpenAI API key configured: {settings.OPENAI_API_KEY[:10]}...")
        else:
            print("OpenAI API key NOT configured or library not installed")

        # Google configuration
        if hasattr(settings, 'GOOGLE_API_KEY') and settings.GOOGLE_API_KEY and genai:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            print(f"Google API key configured: {settings.GOOGLE_API_KEY[:10]}...")
        else:
            print("Google API key NOT configured or library not installed")

        # Perplexity configuration
        if hasattr(settings, 'PERPLEXITY_API_KEY') and settings.PERPLEXITY_API_KEY:
            print(f"Perplexity API key configured: {settings.PERPLEXITY_API_KEY[:10]}...")
        else:
            print("Perplexity API key NOT configured")

    def get_chat_response(self, user_message, session, user, provider=None):
        """Get AI response for user message"""
        # Check for cached response first
        cache_key = self._generate_cache_key(user_message, session.id, provider or 'default')
        if cache_key in AI_RESPONSE_CACHE:
            cache_entry = AI_RESPONSE_CACHE[cache_key]
            # Check if cache entry is still valid (30 minutes)
            if time.time() - cache_entry['timestamp'] < 1800:
                logger.info(f"Returning cached response for session {session.id}")
                return cache_entry['response'], cache_entry['data']
            else:
                # Remove expired cache entry
                del AI_RESPONSE_CACHE[cache_key]

        # Use default provider from settings if none specified
        if not provider:
            provider = getattr(settings, 'DEFAULT_AI_PROVIDER', 'perplexity')

        print(f"Getting chat response using provider: {provider}")

        # Get user's chatbot settings
        from ..models import ChatbotSettings
        try:
            settings_obj = ChatbotSettings.objects.get(user=user)
            provider = provider or settings_obj.preferred_ai_provider
            response_style = settings_obj.response_style
            enable_web_search = settings_obj.enable_web_search
            enable_citations = settings_obj.enable_citations
        except ChatbotSettings.DoesNotExist:
            response_style = 'casual'
            enable_web_search = True
            enable_citations = True

        # Build conversation context
        context = self._build_conversation_context(session, user, response_style)

        start_time = time.time()
        try:
            if provider == 'openai' and OpenAI:
                response, tokens_used = self._get_openai_response(context, user_message)
            elif provider == 'gemini' and genai:
                response, tokens_used = self._get_gemini_response(context, user_message)
            elif provider == 'perplexity':
                response, tokens_used = self._get_perplexity_response(
                    context, user_message, enable_web_search, enable_citations
                )
            else:
                raise ValueError(f"Unsupported or unavailable AI provider: {provider}")

            response_time = time.time() - start_time
            response_data = {
                'provider': provider,
                'response_time': response_time,
                'tokens_used': tokens_used
            }

            # Cache the response for similar queries
            AI_RESPONSE_CACHE[cache_key] = {
                'response': response,
                'data': response_data,
                'timestamp': time.time()
            }

            # Clean old cache entries (keep only last 100 entries)
            if len(AI_RESPONSE_CACHE) > 100:
                oldest_key = min(AI_RESPONSE_CACHE.keys(), 
                               key=lambda k: AI_RESPONSE_CACHE[k]['timestamp'])
                del AI_RESPONSE_CACHE[oldest_key]

            logger.info(f"AI response generated in {response_time:.2f}s using {provider}")
            return response, response_data

        except Exception as e:
            logger.error(f"AI chat service error: {str(e)}")
            fallback_response = self._get_fallback_response(user_message)
            return fallback_response, {'provider': 'fallback', 'response_time': 0, 'tokens_used': 0}

    def _get_perplexity_response(self, context, user_message, enable_web_search=True, enable_citations=True):
        """Get response from Perplexity AI"""
        try:
            print("Making Perplexity API call...")
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }

            # Choose model based on web search requirement
            model = "sonar-pro" if enable_web_search else "llama-3.1-70b-instruct"

            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": context
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.7,
                "top_p": 1,
                "return_citations": enable_citations,
                "return_images": False,
                "return_related_questions": True
            }

            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"Perplexity API error: {response.status_code} - {response.text}")
                raise Exception(f"Perplexity API returned status {response.status_code}")

            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()

            # Get token usage if available
            tokens_used = result.get('usage', {}).get('total_tokens', 0)

            print(f"Perplexity response received: {ai_response[:50]}...")
            print(f"Tokens used: {tokens_used}")

            return ai_response, tokens_used

        except Exception as e:
            print(f"Perplexity API error: {str(e)}")
            raise

    def _get_openai_response(self, context, user_message):
        """Get response from OpenAI with v1.3.5 syntax"""
        try:
            print("Making OpenAI API call...")
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )

            ai_response = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens

            return ai_response, tokens_used

        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            raise

    def _get_gemini_response(self, context, user_message):
        """Get response from Google Gemini with fallback models"""
        models_to_try = [
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-1.0-pro'
        ]

        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(f"{context}\n\nStudent: {user_message}\nStudyBot:")
                
                ai_response = response.text.strip()
                tokens_used = len(context.split()) + len(ai_response.split())
                
                print(f"✅ Using model: {model_name}")
                return ai_response, tokens_used
                
            except Exception as e:
                print(f"❌ {model_name} failed: {e}")
                continue

        raise Exception("All Gemini models failed")

    def _generate_cache_key(self, user_message, session_id, provider):
        """Generate cache key for response caching"""
        message_hash = hashlib.md5(user_message.encode()).hexdigest()
        return f"ai_response_{provider}_{session_id}_{message_hash}"

    def _build_conversation_context(self, session, user, response_style):
        """Build conversation context from session history"""
        from ..models import BotMessage

        # Get recent messages for context
        recent_messages = list(BotMessage.objects.filter(
            session=session
        ).order_by('-created_at')[:10])
        recent_messages = list(reversed(recent_messages))

        # Build context
        context = f"""You are StudyBot, an AI tutor and study assistant. Your role is to help students learn effectively.

User Profile:
- Name: {user.display_name}
- College: {user.college.name if user.college else 'Not specified'}
- Year: {user.get_year_of_study_display() if user.year_of_study else 'Not specified'}

Response Style: {response_style}
- Formal: Use professional academic language
- Casual: Use friendly, conversational tone
- Detailed: Provide comprehensive explanations
- Concise: Keep responses brief and to the point

Guidelines:
1. Be helpful, encouraging, and supportive
2. Provide accurate educational information
3. Use examples and analogies when explaining concepts
4. Ask follow-up questions to better understand student needs
5. Suggest relevant quizzes or study materials when appropriate
6. If you don't know something, admit it and suggest resources

Previous conversation:"""

        for msg in recent_messages[-5:]:  # Last 5 messages for context
            role = "Student" if msg.message_type == 'user' else "StudyBot"
            context += f"\n{role}: {msg.content}"

        return context

    def _get_fallback_response(self, user_message):
        """Get fallback response when AI services fail"""
        fallback_responses = [
            "I'm sorry, I'm having trouble connecting to my AI service right now. Please try again in a moment.",
            "It seems there's a technical issue. Could you please rephrase your question?",
            "I'm experiencing some difficulties at the moment. Would you like to try asking your question differently?",
        ]

        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey']):
            response = "Hello! I'm StudyBot, your AI study assistant. How can I help you with your studies today?"
        elif any(word in message_lower for word in ['help', 'stuck', 'confused']):
            response = "I'd love to help you! Could you tell me more specifically what you're working on or what concept you're having trouble with?"
        elif any(word in message_lower for word in ['quiz', 'test', 'exam']):
            response = "I can help you prepare for quizzes and exams! Would you like me to explain a specific topic, create practice questions, or help you with study strategies?"
        elif any(word in message_lower for word in ['thank', 'thanks']):
            response = "You're welcome! I'm always here to help with your studies. Is there anything else you'd like to know?"
        else:
            response = fallback_responses[0]

        return response
