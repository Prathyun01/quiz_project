from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Main messaging views
    path('', views.inbox, name='inbox'),
    path('conversation/<uuid:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('compose/', views.start_conversation, name='start_conversation'),
    path('create-group/', views.create_group, name='create_group'),
    path('search/', views.search_messages, name='search_messages'),
    
    # Conversation management
    path('conversation/<uuid:conversation_id>/settings/', views.conversation_settings, name='conversation_settings'),
    path('message/<uuid:message_id>/delete/', views.delete_message, name='delete_message'),
    
    # AJAX endpoints
    path('ajax/send-message/', views.ajax_send_message, name='ajax_send_message'),
    path('ajax/mark-as-read/', views.ajax_mark_as_read, name='ajax_mark_as_read'),
    path('ajax/save-draft/', views.ajax_save_draft, name='ajax_save_draft'),
    path('ajax/add-reaction/', views.ajax_add_reaction, name='ajax_add_reaction'),
]
