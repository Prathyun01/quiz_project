from django import template
from django.utils.safestring import mark_safe
import math

register = template.Library()

@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        if total == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def progress_bar_class(percentage):
    """Get Bootstrap progress bar class based on percentage"""
    if percentage >= 80:
        return 'bg-success'
    elif percentage >= 60:
        return 'bg-info'
    elif percentage >= 40:
        return 'bg-warning'
    else:
        return 'bg-danger'

@register.filter
def grade_class(grade):
    """Get CSS class for grade display"""
    grade_classes = {
        'A+': 'text-success',
        'A': 'text-success',
        'B+': 'text-info',
        'B': 'text-info',
        'C': 'text-warning',
        'F': 'text-danger'
    }
    return grade_classes.get(grade, 'text-muted')

@register.filter
def duration_format(duration):
    """Format duration in human readable format"""
    if not duration:
        return "0 minutes"
    
    total_seconds = duration.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 and hours == 0:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    
    return " ".join(parts) if parts else "0 seconds"

@register.simple_tag
def difficulty_badge(difficulty):
    """Generate difficulty badge HTML"""
    badge_classes = {
        'easy': 'badge bg-success',
        'medium': 'badge bg-warning',
        'hard': 'badge bg-danger'
    }
    
    css_class = badge_classes.get(difficulty, 'badge bg-secondary')
    return mark_safe(f'<span class="{css_class}">{difficulty.title()}</span>')

@register.simple_tag
def quiz_status_badge(status):
    """Generate status badge HTML"""
    badge_classes = {
        'in_progress': 'badge bg-warning',
        'completed': 'badge bg-success',
        'abandoned': 'badge bg-secondary'
    }
    
    css_class = badge_classes.get(status, 'badge bg-secondary')
    display_text = status.replace('_', ' ').title()
    return mark_safe(f'<span class="{css_class}">{display_text}</span>')

@register.filter
def stars_rating(score, total=5):
    """Generate star rating based on score"""
    if not score:
        score = 0
    
    # Convert score to 5-star scale
    star_score = (score / 100) * total
    full_stars = int(star_score)
    half_star = (star_score - full_stars) >= 0.5
    empty_stars = total - full_stars - (1 if half_star else 0)
    
    stars_html = []
    
    # Full stars
    for i in range(full_stars):
        stars_html.append('<i class="fas fa-star text-warning"></i>')
    
    # Half star
    if half_star:
        stars_html.append('<i class="fas fa-star-half-alt text-warning"></i>')
    
    # Empty stars
    for i in range(empty_stars):
        stars_html.append('<i class="far fa-star text-muted"></i>')
    
    return mark_safe(''.join(stars_html))

@register.simple_tag
def time_remaining_display(seconds):
    """Display time remaining in MM:SS format"""
    if seconds <= 0:
        return "00:00"
    
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiply value by arg"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divide value by arg"""
    try:
        return int(value) // int(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
