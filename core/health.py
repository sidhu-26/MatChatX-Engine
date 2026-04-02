"""
Health check endpoint for monitoring.
"""

from django.http import JsonResponse
from django.urls import path


def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse(
        {
            "status": "healthy",
            "service": "MatChatX",
            "version": "1.0.0",
        }
    )


urlpatterns = [
    path("", health_check, name="health-check"),
]
