from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/accounts/dashboard/', permanent=False)),
    path('accounts/', include('accounts.urls')),
    path('', include('quiz_app.urls')),  # User AI quiz generation
    path('admin-quiz/', include('admin_quiz.urls')),    
    path('chatbot/', include('chatbot.urls')),
    path('documents/', include('document_manager.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
