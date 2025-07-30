from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Count, Q
import json
import csv
from django.utils import timezone
from .models import ChatSession, BotMessage, ChatbotSettings, QuickAction
from .services.ai_chat_service import AIChatService
from accounts.models import UserActivity

# Simple in-memory rate limiting (per server instance)
RATE_LIMIT_STORAGE = {}

def check_rate_limit(user_id, limit=20, window=60):
    """Simple in-memory rate limiting"""
    current_time = timezone.now().timestamp()
    key = f"rate_limit_{user_id}"
    
    if key not in RATE_LIMIT_STORAGE:
        RATE_LIMIT_STORAGE[key] = []
    
    # Clean old entries
    RATE_LIMIT_STORAGE[key] = [
        timestamp for timestamp in RATE_LIMIT_STORAGE[key] 
        if current_time - timestamp < window
    ]
    
    if len(RATE_LIMIT_STORAGE[key]) >= limit:
        return False
    
    RATE_LIMIT_STORAGE[key].append(current_time)
    return True

@login_required
def chat_interface(request):
    """Main chat interface"""
    # Get or create active session
    active_session = ChatSession.objects.filter(
        user=request.user,
        is_active=True
    ).first()
    
    if not active_session:
        active_session = ChatSession.objects.create(
            user=request.user,
            title="New Chat Session"
        )

    # Get chat messages
    messages_list = list(BotMessage.objects.filter(
        session=active_session
    ).order_by('created_at'))

    # Get quick actions
    quick_actions = list(QuickAction.objects.filter(
        is_active=True
    ).order_by('-usage_count')[:8])

    # Get recent sessions
    recent_sessions = list(ChatSession.objects.filter(
        user=request.user
    ).order_by('-updated_at')[:5])

    # Get or create chatbot settings
    chatbot_settings, created = ChatbotSettings.objects.get_or_create(
        user=request.user
    )

    context = {
        'active_session': active_session,
        'messages': messages_list,
        'quick_actions': quick_actions,
        'recent_sessions': recent_sessions,
        'chatbot_settings': chatbot_settings,
    }

    return render(request, 'chatbot/chat.html', context)

@csrf_exempt
@login_required
def send_message(request):
    """Send message to chatbot via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})

    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        user_message = data.get('message', '').strip()
        quick_action_id = data.get('quick_action_id')
        provider = data.get('provider', 'perplexity')

        if not user_message and not quick_action_id:
            return JsonResponse({'success': False, 'error': 'Message cannot be empty'})

        # Rate limiting
        if not check_rate_limit(request.user.id, limit=20, window=60):
            return JsonResponse({'success': False, 'error': 'Rate limit exceeded'})

        # Get session
        session = ChatSession.objects.get(id=session_id, user=request.user)

        # Handle quick action
        if quick_action_id:
            try:
                quick_action = QuickAction.objects.get(id=quick_action_id, is_active=True)
                user_message = quick_action.prompt_template
                quick_action.increment_usage()
            except QuickAction.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Quick action not found'})

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
            user=request.user,
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

        # Log activity
        UserActivity.objects.create(
            user=request.user,
            action='chatbot_used',
            description=f'Used AI chatbot - {session.title}'
        )

        return JsonResponse({
            'success': True,
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
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def new_session(request):
    """Create a new chat session"""
    session_type = request.GET.get('type', 'general')
    
    # End current active session
    ChatSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
    
    # Create new session
    new_session = ChatSession.objects.create(
        user=request.user,
        session_type=session_type,
        title="New Chat Session"
    )
    
    return redirect('chatbot:chat_interface')

@login_required
def load_session(request, session_id):
    """Load a specific chat session"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    # Make this session active
    ChatSession.objects.filter(user=request.user).update(is_active=False)
    session.is_active = True
    session.save()
    
    return redirect('chatbot:chat_interface')

@login_required
def chat_history(request):
    """Display chat session history"""
    sessions = ChatSession.objects.filter(user=request.user).annotate(
        message_count=Count('messages')
    ).order_by('-updated_at')

    # Pagination
    paginator = Paginator(sessions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'sessions': page_obj.object_list,
    }

    return render(request, 'chatbot/history.html', context)

@csrf_exempt
@login_required
def rate_response(request):
    """Rate a bot response as helpful or not"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})

    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')
        is_helpful = data.get('is_helpful')

        bot_message = BotMessage.objects.get(
            id=message_id,
            session__user=request.user,
            message_type='bot'
        )

        bot_message.is_helpful = is_helpful
        bot_message.save()

        return JsonResponse({'success': True})

    except BotMessage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Message not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def delete_session(request, session_id):
    """Delete a chat session"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Chat session deleted successfully!')
        return redirect('chatbot:chat_history')
    
    return redirect('chatbot:chat_interface')

@login_required
def chatbot_settings(request):
    """Update chatbot settings"""
    settings_obj, created = ChatbotSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        settings_obj.preferred_ai_provider = request.POST.get('preferred_ai_provider', 'perplexity')
        settings_obj.response_style = request.POST.get('response_style', 'casual')
        settings_obj.enable_web_search = request.POST.get('enable_web_search') == 'on'
        settings_obj.enable_citations = request.POST.get('enable_citations') == 'on'
        settings_obj.auto_suggest_questions = request.POST.get('auto_suggest_questions') == 'on'
        settings_obj.max_context_messages = int(request.POST.get('max_context_messages', 10))
        settings_obj.save()
        
        messages.success(request, 'Chatbot settings updated successfully!')
        return redirect('chatbot:chat_interface')

    context = {
        'settings': settings_obj,
    }

    return render(request, 'chatbot/settings.html', context)

@login_required
def export_session(request, session_id):
    """Export chat session as CSV"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="chat_session_{session.id}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'Type', 'Content', 'AI Provider', 'Response Time'])
    
    for message in session.messages.all():
        writer.writerow([
            message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            message.get_message_type_display(),
            message.content,
            message.ai_provider or '',
            message.response_time or ''
        ])
    
    return response
