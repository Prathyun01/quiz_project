from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Updated pattern to properly handle UUIDs
    re_path(r'ws/chatbot/(?P<session_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$', 
            consumers.ChatbotConsumer.as_asgi()),
]
