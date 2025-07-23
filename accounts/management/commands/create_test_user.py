from django.core.management.base import BaseCommand
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Create a test user for login testing'

    def handle(self, *args, **options):
        # Create test user
        if not CustomUser.objects.filter(email='test@example.com').exists():
            user = CustomUser.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123',
                first_name='Test',
                last_name='User',
                is_email_verified=True  # Skip email verification for testing
            )
            self.stdout.write(
                self.style.SUCCESS(f'Test user created successfully!')
            )
            self.stdout.write(f'Email: test@example.com')
            self.stdout.write(f'Username: testuser')
            self.stdout.write(f'Password: testpass123')
        else:
            self.stdout.write(
                self.style.WARNING('Test user already exists')
            )
