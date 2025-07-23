from django import template
from django.utils.html import format_html

register = template.Library()

@register.filter
def chr_filter(value):
    """Convert integer to corresponding ASCII character"""
    try:
        return chr(int(value))
    except (ValueError, TypeError):
        return ''

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

@register.simple_tag
def difficulty_badge(difficulty):
    """Render difficulty badge with appropriate styling"""
    colors = {
        'easy': 'success',
        'medium': 'warning',
        'hard': 'danger'
    }
    color = colors.get(difficulty, 'secondary')
    return format_html(
        '<span class="badge bg-{}">{}</span>',
        color,
        difficulty.title()
    )

@register.simple_tag
def ai_provider_badge(provider):
    """Render AI provider badge with appropriate styling"""
    badges = {
        'gemini': '<span class="badge bg-info"><i class="fab fa-google"></i> Gemini</span>',
        'perplexity': '<span class="badge bg-warning"><i class="fas fa-search"></i> Perplexity</span>',
    }
    return format_html(badges.get(provider, '<span class="badge bg-secondary">Unknown</span>'))

@register.simple_tag
def grade_badge(grade):
    """Render grade badge with appropriate styling"""
    colors = {
        'A+': 'success',
        'A': 'success',
        'B+': 'primary',
        'B': 'primary',
        'C': 'warning',
        'F': 'danger'
    }
    color = colors.get(grade, 'secondary')
    return format_html(
        '<span class="badge bg-{}">{}</span>',
        color,
        grade
    )

@register.filter
def duration_format(duration):
    """Format duration in human readable format"""
    if not duration:
        return "N/A"
    
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

@register.inclusion_tag('quiz_app/partials/quiz_card.html')
def render_quiz_card(quiz, show_actions=True):
    """Render quiz card component"""
    return {
        'quiz': quiz,
        'show_actions': show_actions,
    }

@register.inclusion_tag('quiz_app/partials/question_card.html')
def render_question_card(question, attempt=None, show_answer=False):
    """Render question card component"""
    user_answer = None
    if attempt:
        try:
            user_answer = attempt.useranswer_set.get(question=question)
        except:
            pass
    
    return {
        'question': question,
        'attempt': attempt,
        'user_answer': user_answer,
        'show_answer': show_answer,
    }

@register.inclusion_tag('quiz_app/partials/timer_widget.html')
def render_timer(time_limit_seconds, attempt_id):
    """Render quiz timer widget"""
    return {
        'time_limit_seconds': time_limit_seconds,
        'attempt_id': attempt_id,
    }
