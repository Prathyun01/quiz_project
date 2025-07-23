from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Debug login issues'

    def add_arguments(self, parser):
        parser.add_argument('identifier', type=str, help='Email or username')
        parser.add_argument('password', type=str, help='Password')

    def handle(self, *args, **options):
        identifier = options['identifier']
        password = options['password']
        
        self.stdout.write(f"Testing login for: {identifier}")
        
        # Check if user exists
        try:
            if '@' in identifier:
                user = CustomUser.objects.get(email=identifier)
                self.stdout.write(f"✅ User found by email: {user.email}")
            else:
                user = CustomUser.objects.get(username=identifier)
                self.stdout.write(f"✅ User found by username: {user.username}")
            
            self.stdout.write(f"User ID: {user.id}")
            self.stdout.write(f"Is Active: {user.is_active}")
            self.stdout.write(f"Is Email Verified: {user.is_email_verified}")
            
            # Test password
            if user.check_password(password):
                self.stdout.write(self.style.SUCCESS("✅ Password is correct"))
            else:
                self.stdout.write(self.style.ERROR("❌ Password is incorrect"))
            
            # Test authentication
            auth_user = authenticate(username=identifier, password=password)
            if auth_user:
                self.stdout.write(self.style.SUCCESS("✅ Authentication successful"))
            else:
                self.stdout.write(self.style.ERROR("❌ Authentication failed"))
                
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ User not found: {identifier}"))
