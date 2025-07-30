from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.chat_interface, name='chat_interface'),
    path('new-session/', views.new_session, name='new_session'),
    path('load-session/<uuid:session_id>/', views.load_session, name='load_session'),
    path('history/', views.chat_history, name='chat_history'),
    path('ajax/send-message/', views.send_message, name='send_message'),
    path('ajax/rate-response/', views.rate_response, name='rate_response'),
    path('delete-session/<uuid:session_id>/', views.delete_session, name='delete_session'),
    path('settings/', views.chatbot_settings, name='chatbot_settings'),
    path('export-session/<uuid:session_id>/', views.export_session, name='export_session'),
]
