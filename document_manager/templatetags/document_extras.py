from django import template
from django.utils.safestring import mark_safe
from django.urls import reverse

register = template.Library()

@register.filter
def can_access(document, user):
    """Check if user can access document"""
    if hasattr(document, 'can_access') and callable(document.can_access):
        try:
            return document.can_access(user)
        except Exception:
            # Fallback: public documents are accessible, others require login
            if hasattr(document, 'access_level'):
                if document.access_level == 'public':
                    return True
                elif document.access_level == 'registered':
                    return user.is_authenticated if user else False
                elif document.access_level == 'private':
                    return user == document.uploaded_by if user and hasattr(document, 'uploaded_by') else False
            return False
    
    # Fallback for documents without can_access method
    if hasattr(document, 'access_level'):
        return document.access_level == 'public' or (user and user.is_authenticated)
    
    return True  # Default: allow access

@register.filter
def can_download(document, user):
    """Check if user can download document - alias for can_access"""
    return can_access(document, user)

@register.filter
def file_icon_class(file_extension):
    """Return appropriate CSS class for file type"""
    if not file_extension:
        return 'fas fa-file text-secondary'
    
    ext = str(file_extension).lower()
    if not ext.startswith('.'):
        ext = '.' + ext
    
    icon_map = {
        '.pdf': 'fas fa-file-pdf text-danger',
        '.doc': 'fas fa-file-word text-primary',
        '.docx': 'fas fa-file-word text-primary',
        '.ppt': 'fas fa-file-powerpoint text-warning',
        '.pptx': 'fas fa-file-powerpoint text-warning',
        '.xls': 'fas fa-file-excel text-success',
        '.xlsx': 'fas fa-file-excel text-success',
        '.txt': 'fas fa-file-alt text-secondary',
        '.rtf': 'fas fa-file-alt text-secondary',
        '.jpg': 'fas fa-file-image text-info',
        '.jpeg': 'fas fa-file-image text-info',
        '.png': 'fas fa-file-image text-info',
        '.gif': 'fas fa-file-image text-info',
        '.zip': 'fas fa-file-archive text-warning',
        '.rar': 'fas fa-file-archive text-warning',
        '.mp4': 'fas fa-file-video text-danger',
        '.mp3': 'fas fa-file-audio text-success',
    }
    
    return icon_map.get(ext, 'fas fa-file text-secondary')

@register.filter
def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if not size_bytes:
        return "Unknown"
    
    try:
        size_bytes = int(size_bytes)
    except (ValueError, TypeError):
        return "Unknown"
    
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

@register.filter
def stars_display(rating):
    """Display star rating as HTML"""
    if not rating:
        rating = 0
    
    try:
        rating = float(rating)
    except (ValueError, TypeError):
        rating = 0
    
    stars_html = ""
    for i in range(1, 6):
        if i <= rating:
            stars_html += '<i class="fas fa-star text-warning"></i>'
        elif i - 0.5 <= rating:
            stars_html += '<i class="fas fa-star-half-alt text-warning"></i>'
        else:
            stars_html += '<i class="far fa-star text-muted"></i>'
    
    return mark_safe(stars_html)

@register.filter
def access_level_badge_class(access_level):
    """Return Bootstrap badge class for access level"""
    badge_map = {
        'public': 'bg-success',
        'registered': 'bg-primary',
        'premium': 'bg-warning',
        'private': 'bg-secondary',
    }
    return badge_map.get(access_level, 'bg-secondary')

@register.simple_tag
def document_share_url(document, request=None):
    """Generate shareable URL for document"""
    if request:
        return request.build_absolute_uri(
            reverse('document_manager:document_detail', kwargs={'document_id': document.id})
        )
    return reverse('document_manager:document_detail', kwargs={'document_id': document.id})

@register.simple_tag
def document_download_url(document):
    """Generate download URL for document"""
    return reverse('document_manager:download_document', kwargs={'document_id': document.id})

@register.inclusion_tag('document_manager/partials/document_stats.html')
def document_stats(document):
    """Render document statistics partial"""
    return {
        'document': document,
        'download_count': getattr(document, 'download_count', 0),
        'view_count': getattr(document, 'view_count', 0),
        'average_rating': getattr(document, 'average_rating', 0),
    }

@register.inclusion_tag('document_manager/partials/share_buttons.html')
def share_buttons(document, user=None):
    """Render share buttons partial"""
    return {
        'document': document,
        'user': user,
    }
