"""
Management command to create a test LIVE match for immediate testing.

Usage:
    python manage.py create_live_match
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from matches.models import Match, MatchStatus


class Command(BaseCommand):
    help = "Create a test match that is LIVE right now for immediate testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--team1",
            type=str,
            default="CSK",
            help="Team 1 name (default: CSK)",
        )
        parser.add_argument(
            "--team2",
            type=str,
            default="MI",
            help="Team 2 name (default: MI)",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        team_1 = options["team1"]
        team_2 = options["team2"]

        match = Match.objects.create(
            team_1=team_1,
            team_2=team_2,
            start_time=now - timedelta(minutes=10),
            end_time=now + timedelta(hours=3),
            status=MatchStatus.LIVE,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🏏 LIVE match created!\n\n"
                f"   {match.team_1} vs {match.team_2}\n"
                f"   Match ID: {match.id}\n"
                f"   Status: {match.status}\n\n"
                f"   WebSocket URL:\n"
                f"   ws://localhost:8000/ws/chat/{match.id}/\n"
            )
        )
