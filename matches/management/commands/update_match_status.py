"""
Management command to update match statuses.

Usage:
    python manage.py update_match_status

Can be run as a cron job or periodic task.
"""

from django.core.management.base import BaseCommand

from matches.services import update_match_statuses
from matches.models import Match, MatchStatus


class Command(BaseCommand):
    help = "Update match statuses based on current time (UPCOMING→LIVE→CLOSED)"

    def handle(self, *args, **options):
        self.stdout.write("🔄 Updating match statuses...")

        result = update_match_statuses()

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Transitions: "
                f"{result['upcoming_to_live']} UPCOMING→LIVE, "
                f"{result['live_to_closed']} LIVE→CLOSED"
            )
        )

        # Summary
        for status in MatchStatus:
            count = Match.objects.filter(status=status).count()
            self.stdout.write(f"   {status.label}: {count}")
