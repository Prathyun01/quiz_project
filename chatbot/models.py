import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class ChatSession(models.Model):
    SESSION_TYPE_CHOICES = [
        ('study_help', 'Study Help'),
        ('quiz_explanation', 'Quiz Explanation'),
        ('general', 'General Chat'),  # Shortened from 'general_chat'
        ('homework_help', 'Homework Help'),
        ('concept_help', 'Concept Help'),  # Shortened from 'concept_clarification'
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=255, default="New Chat Session")
    session_type = models.CharField(max_length=25, choices=SESSION_TYPE_CHOICES, default='general')  # Increased max_length
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.display_name} - {self.title}"

    @property
    def message_count(self):
        return self.messages.count()

    
    @property
    def last_message_time(self):
        last_message = self.messages.order_by('-created_at').first()
        return last_message.created_at if last_message else self.created_at

class BotMessage(models.Model):
    MESSAGE_TYPES = [
        ('user', 'User Message'),
        ('bot', 'Bot Response'),
    ]
    
    AI_PROVIDERS = [
        ('openai', 'OpenAI GPT'),
        ('gemini', 'Google Gemini'),
        ('perplexity', 'Perplexity AI'),
        ('fallback', 'Fallback Response'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    ai_provider = models.CharField(max_length=20, choices=AI_PROVIDERS, blank=True, null=True)
    response_time = models.FloatField(blank=True, null=True, help_text="Response time in seconds")
    tokens_used = models.IntegerField(blank=True, null=True)
    is_helpful = models.BooleanField(blank=True, null=True, help_text="User feedback on bot response")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f"{self.get_message_type_display()}: {self.content[:50]}..."
    
    @property
    def is_bot_message(self):
        return self.message_type == 'bot'
    
    @property
    def is_user_message(self):
        return self.message_type == 'user'

class ChatbotSettings(models.Model):
    AI_PROVIDERS = [
        ('openai', 'OpenAI GPT'),
        ('gemini', 'Google Gemini'),
        ('perplexity', 'Perplexity AI'),
    ]
    
    RESPONSE_STYLES = [
        ('formal', 'Formal'),
        ('casual', 'Casual'),
        ('detailed', 'Detailed'),
        ('concise', 'Concise'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chatbot_settings')
    preferred_ai_provider = models.CharField(max_length=20, choices=AI_PROVIDERS, default='perplexity')
    response_style = models.CharField(max_length=20, choices=RESPONSE_STYLES, default='casual')
    enable_web_search = models.BooleanField(default=True, help_text="Enable real-time web search for responses")
    enable_citations = models.BooleanField(default=True, help_text="Include source citations in responses")
    max_context_messages = models.IntegerField(default=10, help_text="Number of previous messages to include as context")
    auto_suggest_questions = models.BooleanField(default=True, help_text="Automatically suggest follow-up questions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Chatbot Settings"
        verbose_name_plural = "Chatbot Settings"
        
    def __str__(self):
        return f"Settings for {self.user.display_name}"

class QuickAction(models.Model):
    title = models.CharField(max_length=100)
    prompt_template = models.TextField(help_text="Template for the prompt that will be sent to AI")
    icon = models.CharField(max_length=50, default='fas fa-question-circle', help_text="FontAwesome icon class")
    category = models.CharField(max_length=50, choices=[
        ('study', 'Study Help'),
        ('math', 'Mathematics'),
        ('science', 'Science'),
        ('language', 'Language Arts'),
        ('general', 'General'),
    ], default='general')
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-usage_count', 'title']
        
    def __str__(self):
        return self.title
    
    def increment_usage(self):
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
