from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import ChatSession, BotMessage, ChatbotSettings, QuickAction

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'session_type', 'message_count_display', 'is_active', 'created_at', 'last_activity']
    list_filter = ['session_type', 'is_active', 'created_at', 'updated_at']
    search_fields = ['title', 'user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'message_count_display', 'last_message_preview']
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'title', 'session_type', 'is_active')
        }),
        ('Statistics', {
            'fields': ('message_count_display', 'last_message_preview'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user').prefetch_related('messages')
        return queryset.annotate(
            message_count=Count('messages'),
            bot_message_count=Count('messages', filter=Q(messages__message_type='bot')),
            user_message_count=Count('messages', filter=Q(messages__message_type='user'))
        )
    
    def message_count_display(self, obj):
        if hasattr(obj, 'message_count'):
            return format_html(
                '<span title="Total: {} | User: {} | Bot: {}">📊 {}</span>',
                obj.message_count,
                obj.user_message_count,
                obj.bot_message_count,
                obj.message_count
            )
        return obj.message_count
    message_count_display.short_description = 'Messages'
    message_count_display.admin_order_field = 'message_count'
    
    def last_activity(self, obj):
        return obj.last_message_time
    last_activity.short_description = 'Last Activity'
    last_activity.admin_order_field = 'updated_at'
    
    def last_message_preview(self, obj):
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            preview = last_message.content[:100] + '...' if len(last_message.content) > 100 else last_message.content
            return format_html(
                '<div style="max-width: 300px;"><strong>{}:</strong> {}</div>',
                last_message.get_message_type_display(),
                preview
            )
        return "No messages yet"
    last_message_preview.short_description = 'Last Message Preview'

@admin.register(BotMessage)
class BotMessageAdmin(admin.ModelAdmin):
    list_display = ['session_title', 'message_type', 'content_preview', 'ai_provider', 'response_time', 'is_helpful', 'created_at']
    list_filter = ['message_type', 'ai_provider', 'is_helpful', 'created_at', 'session__session_type']
    search_fields = ['content', 'session__title', 'session__user__username']
    readonly_fields = ['id', 'created_at', 'content_preview_full']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        ('Message Details', {
            'fields': ('id', 'session', 'message_type', 'content', 'content_preview_full')
        }),
        ('AI Response Data', {
            'fields': ('ai_provider', 'response_time', 'tokens_used', 'is_helpful'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'session__user')
    
    def session_title(self, obj):
        return format_html(
            '<a href="/admin/chatbot/chatsession/{}/change/" target="_blank">{}</a>',
            obj.session.id,
            obj.session.title
        )
    session_title.short_description = 'Session'
    session_title.admin_order_field = 'session__title'
    
    def content_preview(self, obj):
        preview = obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
        return format_html('<div style="max-width: 200px;">{}</div>', preview)
    content_preview.short_description = 'Content'
    
    def content_preview_full(self, obj):
        return format_html('<div style="max-width: 500px; white-space: pre-wrap;">{}</div>', obj.content)
    content_preview_full.short_description = 'Full Content Preview'
    
    def response_time(self, obj):
        if obj.response_time:
            return f"{obj.response_time:.2f}s"
        return "-"
    response_time.short_description = 'Response Time'
    response_time.admin_order_field = 'response_time'

@admin.register(ChatbotSettings)
class ChatbotSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_ai_provider', 'response_style', 'enable_web_search', 'enable_citations', 'updated_at']
    list_filter = ['preferred_ai_provider', 'response_style', 'enable_web_search', 'enable_citations']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('AI Configuration', {
            'fields': ('preferred_ai_provider', 'response_style', 'max_context_messages')
        }),
        ('Features', {
            'fields': ('enable_web_search', 'enable_citations', 'auto_suggest_questions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(QuickAction)
class QuickActionAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'usage_count', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'prompt_template']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Quick Action Details', {
            'fields': ('title', 'prompt_template', 'icon', 'category', 'is_active')
        }),
        ('Statistics', {
            'fields': ('usage_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['reset_usage_count', 'duplicate_quick_action']
    
    def reset_usage_count(self, request, queryset):
        updated = queryset.update(usage_count=0)
        self.message_user(request, f'Reset usage count for {updated} quick actions.')
    reset_usage_count.short_description = "Reset usage count"
    
    def duplicate_quick_action(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.title = f"{obj.title} (Copy)"
            obj.usage_count = 0
            obj.save()
        self.message_user(request, f'Duplicated {queryset.count()} quick actions.')
    duplicate_quick_action.short_description = "Duplicate selected quick actions"
