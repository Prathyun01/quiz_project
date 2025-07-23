from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max, Prefetch
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
import json
import uuid

from .models import Conversation, Message, MessageStatus, MessageReaction, ConversationSettings, MessageDraft
from .forms import MessageForm, NewConversationForm, GroupConversationForm, ConversationSettingsForm, MessageSearchForm
from .services.message_service import MessageService
from .services.notification_service import NotificationService

User = get_user_model()

@login_required
def inbox(request):
    """Display user's conversation inbox"""
    # Get user's conversations with latest message info
    conversations = Conversation.objects.filter(
        participants=request.user
    ).prefetch_related(
        'participants',
        Prefetch('message_set', queryset=Message.objects.order_by('-created_at'))
    ).annotate(
        last_message_time=Max('message__created_at'),
        unread_count=Count('message__status_set', filter=Q(
            message__status_set__recipient=request.user,
            message__status_set__is_read=False
        ))
    ).order_by('-last_message_time')
    
    # Apply filters
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        conversations = conversations.filter(unread_count__gt=0)
    elif filter_type == 'groups':
        conversations = conversations.filter(is_group=True)
    elif filter_type == 'direct':
        conversations = conversations.filter(is_group=False)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        conversations = conversations.filter(
            Q(group_name__icontains=search_query) |
            Q(participants__first_name__icontains=search_query) |
            Q(participants__last_name__icontains=search_query) |
            Q(participants__username__icontains=search_query)
        ).distinct()
    
    # Pagination
    paginator = Paginator(conversations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get total unread count
    total_unread = MessageStatus.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    context = {
        'page_obj': page_obj,
        'conversations': page_obj.object_list,
        'filter_type': filter_type,
        'search_query': search_query,
        'total_unread': total_unread,
    }
    return render(request, 'messaging/inbox.html', context)

@login_required
def conversation_detail(request, conversation_id):
    """Display conversation messages"""
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related('participants'),
        id=conversation_id,
        participants=request.user
    )
    
    # Mark messages as read
    conversation.mark_as_read(request.user)
    
    # Get messages with related data
    messages_list = Message.objects.filter(
        conversation=conversation,
        is_deleted=False
    ).select_related('sender', 'reply_to__sender').prefetch_related(
        'reactions__user',
        'status_set'
    ).order_by('created_at')
    
    # Pagination
    paginator = Paginator(messages_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Handle message sending
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            
            # Determine message type
            if message.attachment:
                if message.attachment.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    message.message_type = 'image'
                else:
                    message.message_type = 'file'
            
            message.save()
            
            # Create message status for all participants except sender
            participants = conversation.participants.exclude(id=request.user.id)
            MessageService.create_message_statuses(message, participants)
            
            # Send notifications
            NotificationService.send_new_message_notifications(message)
            
            # Update conversation timestamp
            conversation.updated_at = timezone.now()
            conversation.save()
            
            messages.success(request, 'Message sent successfully!')
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()
        
        # Load draft if exists
        try:
            draft = MessageDraft.objects.get(conversation=conversation, user=request.user)
            form.fields['content'].initial = draft.content
        except MessageDraft.DoesNotExist:
            pass
    
    # Get conversation settings
    try:
        conv_settings = ConversationSettings.objects.get(
            conversation=conversation,
            user=request.user
        )
    except ConversationSettings.DoesNotExist:
        conv_settings = None
    
    # Get other participants for display
    other_participants = conversation.participants.exclude(id=request.user.id)
    
    context = {
        'conversation': conversation,
        'page_obj': page_obj,
        'messages': page_obj.object_list,
        'form': form,
        'other_participants': other_participants,
        'conv_settings': conv_settings,
    }
    return render(request, 'messaging/conversation.html', context)

@login_required
def start_conversation(request):
    """Start a new conversation"""
    if request.method == 'POST':
        form = NewConversationForm(request.user, request.POST)
        if form.is_valid():
            recipient = form.cleaned_data['recipient']
            initial_message = form.cleaned_data['initial_message']
            
            # Check if conversation already exists
            existing_conv = Conversation.objects.filter(
                is_group=False,
                participants=request.user
            ).filter(participants=recipient).first()
            
            if existing_conv:
                # Redirect to existing conversation
                return redirect('messaging:conversation_detail', conversation_id=existing_conv.id)
            
            # Create new conversation
            conversation = Conversation.objects.create(is_group=False)
            conversation.participants.add(request.user, recipient)
            
            # Send initial message if provided
            if initial_message.strip():
                message = Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=initial_message.strip()
                )
                
                # Create message status for recipient
                MessageService.create_message_statuses(message, [recipient])
                
                # Send notification
                NotificationService.send_new_message_notifications(message)
            
            messages.success(request, f'Conversation started with {recipient.display_name}!')
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    else:
        form = NewConversationForm(request.user)
    
    context = {
        'form': form,
        'title': 'Start New Conversation',
    }
    return render(request, 'messaging/compose.html', context)

@login_required
def create_group(request):
    """Create a group conversation"""
    if request.method == 'POST':
        form = GroupConversationForm(request.user, request.POST)
        if form.is_valid():
            conversation = form.save(commit=False)
            conversation.is_group = True
            conversation.group_admin = request.user
            conversation.save()
            
            # Add participants
            participants = form.cleaned_data['participants']
            conversation.participants.add(request.user)  # Add creator
            conversation.participants.add(*participants)
            
            # Create system message
            system_message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                message_type='system',
                content=f'{request.user.display_name} created the group "{conversation.group_name}"'
            )
            
            # Create message statuses for all participants
            all_participants = list(participants) + [request.user]
            MessageService.create_message_statuses(system_message, all_participants)
            
            messages.success(request, f'Group "{conversation.group_name}" created successfully!')
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    else:
        form = GroupConversationForm(request.user)
    
    context = {
        'form': form,
        'title': 'Create Group Chat',
    }
    return render(request, 'messaging/compose.html', context)

@login_required
def search_messages(request):
    """Search messages across conversations"""
    form = MessageSearchForm(request.user, request.GET)
    results = Message.objects.none()
    
    if form.is_valid() and form.cleaned_data.get('query'):
        query = form.cleaned_data['query']
        conversation = form.cleaned_data.get('conversation')
        message_type = form.cleaned_data.get('message_type')
        
        # Base query - user's conversations only
        results = Message.objects.filter(
            conversation__participants=request.user,
            is_deleted=False,
            content__icontains=query
        ).select_related('conversation', 'sender').order_by('-created_at')
        
        # Apply filters
        if conversation:
            results = results.filter(conversation=conversation)
        
        if message_type:
            results = results.filter(message_type=message_type)
        
        # Pagination
        paginator = Paginator(results, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    else:
        page_obj = None
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'results': page_obj.object_list if page_obj else [],
        'query': form.cleaned_data.get('query') if form.is_valid() else '',
    }
    return render(request, 'messaging/search.html', context)

@csrf_exempt
@login_required
def ajax_send_message(request):
    """AJAX endpoint for sending messages"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        content = data.get('content', '').strip()
        reply_to_id = data.get('reply_to_id')
        
        if not conversation_id or not content:
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        # Get conversation
        conversation = Conversation.objects.get(
            id=conversation_id,
            participants=request.user
        )
        
        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
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
        
        # Create message statuses
        participants = conversation.participants.exclude(id=request.user.id)
        MessageService.create_message_statuses(message, participants)
        
        # Send notifications
        NotificationService.send_new_message_notifications(message)
        
        # Update conversation
        conversation.updated_at = timezone.now()
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': str(message.id),
                'content': message.content,
                'sender': message.sender.display_name,
                'created_at': message.created_at.isoformat(),
            }
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required
def ajax_mark_as_read(request):
    """AJAX endpoint to mark messages as read"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        
        conversation = Conversation.objects.get(
            id=conversation_id,
            participants=request.user
        )
        
        conversation.mark_as_read(request.user)
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required
def ajax_save_draft(request):
    """AJAX endpoint to save message drafts"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        content = data.get('content', '').strip()
        
        conversation = Conversation.objects.get(
            id=conversation_id,
            participants=request.user
        )
        
        if content:
            MessageDraft.objects.update_or_create(
                conversation=conversation,
                user=request.user,
                defaults={'content': content}
            )
        else:
            # Delete draft if content is empty
            MessageDraft.objects.filter(
                conversation=conversation,
                user=request.user
            ).delete()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required
def ajax_add_reaction(request):
    """AJAX endpoint to add/remove message reactions"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')
        reaction_type = data.get('reaction_type')
        
        message = Message.objects.get(
            id=message_id,
            conversation__participants=request.user
        )
        
        # Toggle reaction
        reaction, created = MessageReaction.objects.get_or_create(
            message=message,
            user=request.user,
            defaults={'reaction_type': reaction_type}
        )
        
        if not created:
            if reaction.reaction_type == reaction_type:
                # Remove reaction if same type
                reaction.delete()
                action = 'removed'
            else:
                # Update reaction type
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
        
        return JsonResponse({
            'success': True,
            'action': action,
            'reaction_counts': reaction_counts
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def conversation_settings(request, conversation_id):
    """Manage conversation settings"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )
    
    # Get or create settings
    settings_obj, created = ConversationSettings.objects.get_or_create(
        conversation=conversation,
        user=request.user
    )
    
    if request.method == 'POST':
        form = ConversationSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully!')
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    else:
        form = ConversationSettingsForm(instance=settings_obj)
    
    context = {
        'conversation': conversation,
        'form': form,
        'settings': settings_obj,
    }
    return render(request, 'messaging/settings.html', context)

@login_required
def delete_message(request, message_id):
    """Delete a message (soft delete)"""
    message = get
