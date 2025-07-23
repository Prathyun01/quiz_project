from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Conversation, Message, MessageStatus, MessageReaction, ConversationSettings, MessageDraft

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation_type', 'participant_count', 'message_count', 'last_message_time', 'created_at']
    list_filter = ['is_group', 'created_at']
    search_fields = ['group_name', 'participants__username', 'participants__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['participants']
    
    def conversation_type(self, obj):
        return "Group" if obj.is_group else "Direct"
    conversation_type.short_description = 'Type'
    
    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'
    
    def message_count(self, obj):
        return obj.message_set.count()
    message_count.short_description = 'Messages'
    
    def last_message_time(self, obj):
        last_msg = obj.last_message
        return last_msg.created_at if last_msg else 'No messages'
    last_message_time.short_description = 'Last Message'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'conversation_type', 'message_type', 'content_preview', 'has_attachment', 'created_at']
    list_filter = ['message_type', 'is_edited', 'is_deleted', 'created_at']
    search_fields = ['content', 'sender__username', 'conversation__group_name']
    readonly_fields = ['id', 'created_at', 'edited_at', 'deleted_at']
    
    def conversation_type(self, obj):
        return "Group" if obj.conversation.is_group else "Direct"
    conversation_type.short_description = 'Conv. Type'
    
    def content_preview(self, obj):
        if obj.is_deleted:
            return format_html('<em style="color: red;">Deleted message</em>')
        elif obj.content:
            preview = obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
            return format_html('<span title="{}">{}</span>', obj.content, preview)
        return '-'
    content_preview.short_description = 'Content'
    
    def has_attachment(self, obj):
        if obj.attachment:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    has_attachment.short_description = 'Attachment'

@admin.register(MessageStatus)
class MessageStatusAdmin(admin.ModelAdmin):
    list_display = ['message_id', 'recipient', 'is_delivered', 'delivered_at', 'is_read', 'read_at']
    list_filter = ['is_delivered', 'is_read']
    search_fields = ['recipient__username', 'message__content']
    readonly_fields = ['delivered_at', 'read_at']

@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ['message_id', 'user', 'reaction_display', 'created_at']
    list_filter = ['reaction_type', 'created_at']
    search_fields = ['user__username', 'message__content']
    
    def reaction_display(self, obj):
        return f"{obj.get_reaction_type_display()} {dict(obj.REACTION_TYPES)[obj.reaction_type]}"
    reaction_display.short_description = 'Reaction'

@admin.register(ConversationSettings)
class ConversationSettingsAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'user', 'is_muted', 'is_archived', 'is_pinned']
    list_filter = ['is_muted', 'is_archived', 'is_pinned']
    search_fields = ['user__username', 'conversation__group_name']

@admin.register(MessageDraft)
class MessageDraftAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'user', 'content_preview', 'updated_at']
    search_fields = ['user__username', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    def content_preview(self, obj):
        preview = obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        return format_html('<span title="{}">{}</span>', obj.content, preview)
    content_preview.short_description = 'Content'
