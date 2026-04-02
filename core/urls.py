"""
MatChatX URL Configuration
"""

from django.urls import path, include

urlpatterns = [
    path("matches/", include("matches.urls")),
    path("api/health/", include("core.health")),
]
