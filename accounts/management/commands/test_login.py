from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Test login functionality'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username or email to test')
        parser.add_argument('--password', type=str, help='Password to test')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        
        if not username or not password:
            self.stdout.write(self.style.ERROR('Please provide both username and password'))
            return
        
        # Test authentication
        user = authenticate(username=username, password=password)
        
        if user:
            self.stdout.write(self.style.SUCCESS(f'✅ Authentication successful for: {user.email}'))
            self.stdout.write(f'User ID: {user.id}')
            self.stdout.write(f'Is Active: {user.is_active}')
            self.stdout.write(f'Is Email Verified: {user.is_email_verified}')
        else:
            self.stdout.write(self.style.ERROR('❌ Authentication failed'))
            
            # Try to find the user
            try:
                user = CustomUser.objects.get(email=username)
                self.stdout.write(f'User found by email: {user.email}')
                self.stdout.write(f'Is Active: {user.is_active}')
            except CustomUser.DoesNotExist:
                try:
                    user = CustomUser.objects.get(username=username)
                    self.stdout.write(f'User found by username: {user.username}')
                    self.stdout.write(f'Is Active: {user.is_active}')
                except CustomUser.DoesNotExist:
                    self.stdout.write('User not found in database')
