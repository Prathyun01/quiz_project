#!/usr/bin/env python
"""
Development setup script for StudyHub
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quiz_project.settings")
    django.setup()
    
    commands = [
        ['makemigrations'],
        ['migrate'],
        ['collectstatic', '--noinput'],
        ['createsuperuser', '--noinput'] if os.getenv('DJANGO_SUPERUSER_EMAIL') else ['createsuperuser'],
    ]
    
    for cmd in commands:
        print(f"Running: python manage.py {' '.join(cmd)}")
        execute_from_command_line(['manage.py'] + cmd)
    
    print("\n✅ Development environment setup complete!")
    print("🚀 Run: python manage.py runserver")



