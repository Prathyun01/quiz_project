from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import College
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for development'

    def handle(self, *args, **options):
        # Create colleges
        colleges_data = [
            {'name': 'Massachusetts Institute of Technology', 'code': 'MIT', 'location': 'Cambridge, MA'},
            {'name': 'Stanford University', 'code': 'STAN', 'location': 'Stanford, CA'},
            {'name': 'Harvard University', 'code': 'HARV', 'location': 'Cambridge, MA'},
            {'name': 'California Institute of Technology', 'code': 'CALT', 'location': 'Pasadena, CA'},
            {'name': 'University of California Berkeley', 'code': 'UCB', 'location': 'Berkeley, CA'},
        ]
        
        for college_data in colleges_data:
            college, created = College.objects.get_or_create(
                code=college_data['code'],
                defaults=college_data
            )
            if created:
                self.stdout.write(f'Created college: {college.name}')

        # Create sample users
        sample_users = [
            {'username': 'john_doe', 'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'},
            {'username': 'jane_smith', 'email': 'jane@example.com', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'username': 'bob_wilson', 'email': 'bob@example.com', 'first_name': 'Bob', 'last_name': 'Wilson'},
        ]
        
        for user_data in sample_users:
            if not User.objects.filter(username=user_data['username']).exists():
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    password='password123',
                    is_email_verified=True,
                    college=random.choice(College.objects.all()),
                    year_of_study=random.choice(['1', '2', '3', '4'])
                )
                self.stdout.write(f'Created user: {user.username}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
