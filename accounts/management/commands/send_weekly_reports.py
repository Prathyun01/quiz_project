from django.core.management.base import BaseCommand
from accounts.tasks import send_weekly_report

class Command(BaseCommand):
    help = 'Send weekly reports to all active users'

    def handle(self, *args, **options):
        result = send_weekly_report.delay()
        self.stdout.write(
            self.style.SUCCESS(f'Weekly reports task started: {result.id}')
        )
