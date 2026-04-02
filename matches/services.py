"""
Match Lifecycle Service

Handles automatic status transitions based on time:
  - UPCOMING → LIVE: 30 min before start_time
  - LIVE → CLOSED: 30 min after end_time
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.db.models import Q, QuerySet
from django.utils import timezone

from .models import Match, MatchStatus

logger = logging.getLogger("matches")

BUFFER_MINUTES = getattr(settings, "MATCH_BUFFER_MINUTES", 30)


def update_match_statuses() -> dict:
    """
    Bulk-update match statuses based on current time.

    Returns a dict with counts of transitions made.
    """
    now = timezone.now()
    buffer = timedelta(minutes=BUFFER_MINUTES)

    # UPCOMING → LIVE: 30 min before start_time
    live_threshold = now + buffer
    upcoming_to_live = Match.objects.filter(
        status=MatchStatus.UPCOMING,
        start_time__lte=live_threshold,
    ).update(status=MatchStatus.LIVE)

    if upcoming_to_live:
        logger.info(f"Transitioned {upcoming_to_live} match(es) UPCOMING → LIVE")

    # LIVE → CLOSED: 30 min after end_time
    closed_threshold = now - buffer
    live_to_closed = Match.objects.filter(
        status=MatchStatus.LIVE,
        end_time__lte=closed_threshold,
    ).update(status=MatchStatus.CLOSED)

    if live_to_closed:
        logger.info(f"Transitioned {live_to_closed} match(es) LIVE → CLOSED")

    return {
        "upcoming_to_live": upcoming_to_live,
        "live_to_closed": live_to_closed,
    }


def get_live_matches() -> QuerySet:
    """
    Get all currently LIVE matches.

    Triggers status update before querying to ensure freshness.
    """
    update_match_statuses()
    return Match.objects.filter(status=MatchStatus.LIVE).order_by("start_time")


def get_match_by_id(match_id: str) -> Match | None:
    """
    Retrieve a match by ID, updating its status if needed.
    """
    update_match_statuses()
    try:
        return Match.objects.get(id=match_id)
    except Match.DoesNotExist:
        return None


def is_match_live(match_id: str) -> bool:
    """Check if a specific match is currently LIVE."""
    match = get_match_by_id(match_id)
    return match is not None and match.is_live


def get_match_ttl_seconds(match: Match) -> int:
    """
    Calculate TTL for Redis keys based on match end_time + buffer.

    Returns seconds until data should expire.
    """
    buffer = timedelta(minutes=BUFFER_MINUTES)
    expiry_time = match.end_time + buffer
    now = timezone.now()

    remaining = (expiry_time - now).total_seconds()
    return max(int(remaining), 60)  # Minimum 60 seconds TTL
