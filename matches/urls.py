"""
Match URL Configuration
"""

from django.urls import path
from .views import LiveMatchesView

urlpatterns = [
    path("live/", LiveMatchesView.as_view(), name="live-matches"),
]
