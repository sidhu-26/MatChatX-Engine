"""
Match Model

Stores match metadata in PostgreSQL. Chat messages are stored in Redis only.
"""

import uuid
from django.db import models
from django.utils import timezone


class MatchStatus(models.TextChoices):
    UPCOMING = "UPCOMING", "Upcoming"
    LIVE = "LIVE", "Live"
    CLOSED = "CLOSED", "Closed"


class Match(models.Model):
    """
    Represents a sports match.

    Lifecycle:
        UPCOMING → LIVE (30 min before start_time)
        LIVE → CLOSED (30 min after end_time)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team_1 = models.CharField(max_length=100)
    team_2 = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=10,
        choices=MatchStatus.choices,
        default=MatchStatus.UPCOMING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_time"]
        verbose_name = "Match"
        verbose_name_plural = "Matches"
        indexes = [
            models.Index(fields=["status", "start_time"]),
        ]

    def __str__(self):
        return f"{self.team_1} vs {self.team_2} ({self.status})"

    @property
    def is_live(self):
        """Check if match is currently live."""
        return self.status == MatchStatus.LIVE

    @property
    def display_name(self):
        return f"{self.team_1} vs {self.team_2}"
