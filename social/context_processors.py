from .models import SocialNotification

def social_context(request):
    """Add social context to all templates"""
    context = {}
    
    if request.user.is_authenticated:
        # Get unread notifications count
        unread_notifications = SocialNotification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        context['unread_notifications_count'] = unread_notifications
    
    return context
