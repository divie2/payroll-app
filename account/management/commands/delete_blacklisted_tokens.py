


from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from account.models import Token

class Command(BaseCommand):
    help = 'Displays current time'

    def handle(self, *args, **kwargs):
        expiration_time = timezone.now() - timedelta(
            days=7
        )  # Assuming a 7-day refresh token lifetime
        found_token = Token.objects.filter(blacklisted_at__lte=expiration_time)
        found_token_count = found_token.count()
        found_token.delete()
        self.stdout.write(f"Deleted {found_token_count} blacklisted token")