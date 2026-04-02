"""
Management command to seed test match data.

Usage:
    python manage.py seed_matches
"""

from datetime import datetime, timedelta, timezone as tz

from django.core.management.base import BaseCommand
from django.utils import timezone

from matches.models import Match, MatchStatus


# IST offset (+5:30)
IST = tz(timedelta(hours=5, minutes=30))


class Command(BaseCommand):
    help = "Seed the database with IPL match data for testing"

    def handle(self, *args, **options):
        now = timezone.now()

        matches_data = [
            # Today's match — KKR vs SRH (7:30 PM IST, Apr 2)
            {
                "team_1": "KKR",
                "team_2": "SRH",
                "start_time": datetime(2026, 4, 2, 19, 30, tzinfo=IST),
            },
            # Tomorrow — CSK vs PBKS (7:30 PM IST, Apr 3)
            {
                "team_1": "CSK",
                "team_2": "PBKS",
                "start_time": datetime(2026, 4, 3, 19, 30, tzinfo=IST),
            },
            # Apr 4 afternoon — DC vs MI (3:30 PM IST)
            {
                "team_1": "DC",
                "team_2": "MI",
                "start_time": datetime(2026, 4, 4, 15, 30, tzinfo=IST),
            },
            # Apr 4 evening — GT vs RR (7:30 PM IST)
            {
                "team_1": "GT",
                "team_2": "RR",
                "start_time": datetime(2026, 4, 4, 19, 30, tzinfo=IST),
            },
            # Apr 5 afternoon — SRH vs LSG (3:30 PM IST)
            {
                "team_1": "SRH",
                "team_2": "LSG",
                "start_time": datetime(2026, 4, 5, 15, 30, tzinfo=IST),
            },
            # Apr 5 evening — RCB vs CSK (7:30 PM IST)
            {
                "team_1": "RCB",
                "team_2": "CSK",
                "start_time": datetime(2026, 4, 5, 19, 30, tzinfo=IST),
            },
        ]

        created_count = 0

        for data in matches_data:
            start = data["start_time"]
            end = start + timedelta(hours=4)  # ~4 hour match duration

            # Auto-calculate status based on current time + 30 min buffer
            buffer = timedelta(minutes=30)
            if now >= (start - buffer) and now <= (end + buffer):
                status = MatchStatus.LIVE
            elif now < (start - buffer):
                status = MatchStatus.UPCOMING
            else:
                status = MatchStatus.CLOSED

            match, created = Match.objects.get_or_create(
                team_1=data["team_1"],
                team_2=data["team_2"],
                start_time=start,
                defaults={
                    "end_time": end,
                    "status": status,
                },
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ {match.team_1} vs {match.team_2} "
                        f"[{status}] (ID: {match.id})"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  Exists: {match.team_1} vs {match.team_2}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"🏏 Seeding complete! {created_count} matches created."
            )
        )
        self.stdout.write("")

        # Show live matches for quick reference
        live = Match.objects.filter(status=MatchStatus.LIVE)
        if live.exists():
            self.stdout.write(self.style.HTTP_INFO("📡 Live matches:"))
            for m in live:
                self.stdout.write(
                    f"   → {m.team_1} vs {m.team_2}  "
                    f"ws://localhost:8000/ws/chat/{m.id}/"
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  No live matches right now. Status transitions happen "
                    "automatically based on start_time ± 30 min buffer."
                )
            )