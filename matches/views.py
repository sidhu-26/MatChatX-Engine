"""
Match API Views

Stateless, no-auth endpoints for match data.
"""

import json
import logging

from django.http import JsonResponse
from django.views import View

from .services import get_live_matches

logger = logging.getLogger("matches")


class LiveMatchesView(View):
    """
    GET /matches/live/
    Returns all currently LIVE matches.
    """

    def get(self, request):
        matches = get_live_matches()

        data = [
            {
                "id": str(match.id),
                "team_1": match.team_1,
                "team_2": match.team_2,
                "start_time": match.start_time.isoformat(),
                "end_time": match.end_time.isoformat(),
                "status": match.status,
                "display_name": match.display_name,
            }
            for match in matches
        ]

        return JsonResponse(
            {
                "count": len(data),
                "matches": data,
            }
        )
