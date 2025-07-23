from django.core.management.base import BaseCommand
from quiz_app.models import Category

class Command(BaseCommand):
    help = 'Create built-in quiz categories'

    def handle(self, *args, **options):
        categories = [
            ('science', 'Science & Technology', 'fas fa-atom', '#007bff'),
            ('history', 'History', 'fas fa-landmark', '#17a2b8'),
            ('geography', 'Geography', 'fas fa-globe', '#28a745'), 
            ('literature', 'Literature', 'fas fa-book', '#ffc107'),
            ('mathematics', 'Mathematics', 'fas fa-calculator', '#dc3545'),
            ('sports', 'Sports', 'fas fa-football-ball', '#343a40'),
            ('entertainment', 'Entertainment', 'fas fa-film', '#6f42c1'),
            ('business', 'Business', 'fas fa-chart-line', '#6c757d'),
            ('health', 'Health & Medicine', 'fas fa-heartbeat', '#e83e8c'),
            ('arts', 'Arts & Culture', 'fas fa-palette', '#fd7e14'),
            ('programming', 'Programming', 'fas fa-code', '#20c997'),
            ('general', 'General Knowledge', 'fas fa-brain', '#6610f2'),
        ]

        for slug, name, icon, color in categories:
            category, created = Category.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'icon': icon,
                    'color': color,
                    'is_builtin': True,
                    'is_active': True,
                    'description': f'Quizzes related to {name}'
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {name}')
                )
            else:
                self.stdout.write(f'Category already exists: {name}')
