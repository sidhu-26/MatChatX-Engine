"""
Chat Message Validators

Validates incoming WebSocket payloads and enforces business rules.
"""

import re
import logging

logger = logging.getLogger("chat")

# Simple profanity filter (expandable)
PROFANITY_LIST = {
    "fuck", "shit", "damn", "bitch", "ass", "dick", "bastard",
    "crap", "piss", "slut", "whore",
}

# Compile regex for profanity matching (whole words, case-insensitive)
PROFANITY_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in PROFANITY_LIST) + r")\b",
    re.IGNORECASE,
)

MAX_MESSAGE_LENGTH = 500
MAX_USERNAME_LENGTH = 50
MAX_TEAM_LENGTH = 50


class ValidationError(Exception):
    """Custom validation error with error code."""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


def validate_join_payload(data: dict) -> dict:
    """
    Validate the initial join payload from WebSocket connection.

    Expected:
        {
            "username": "Siddaarth",
            "team_supported": "CSK"
        }

    Returns cleaned data dict.
    Raises ValidationError on failure.
    """
    if not isinstance(data, dict):
        raise ValidationError("Payload must be a JSON object", "INVALID_FORMAT")

    username = data.get("username", "").strip()
    team_supported = data.get("team_supported", "").strip()

    if not username:
        raise ValidationError("'username' is required", "MISSING_USERNAME")

    if len(username) > MAX_USERNAME_LENGTH:
        raise ValidationError(
            f"Username must be {MAX_USERNAME_LENGTH} chars or less",
            "USERNAME_TOO_LONG",
        )

    if not team_supported:
        raise ValidationError("'team_supported' is required", "MISSING_TEAM")

    if len(team_supported) > MAX_TEAM_LENGTH:
        raise ValidationError(
            f"Team name must be {MAX_TEAM_LENGTH} chars or less",
            "TEAM_TOO_LONG",
        )

    return {
        "username": username,
        "team_supported": team_supported,
    }


def validate_message_payload(data: dict) -> dict:
    """
    Validate an incoming chat message.

    Expected:
        {
            "username": "Siddaarth",
            "team": "CSK",
            "message": "Dhoni 🔥"
        }

    Returns cleaned data dict.
    Raises ValidationError on failure.
    """
    if not isinstance(data, dict):
        raise ValidationError("Payload must be a JSON object", "INVALID_FORMAT")

    message = data.get("message", "").strip()
    username = data.get("username", "").strip()
    team = data.get("team", "").strip()

    if not message:
        raise ValidationError("Message cannot be empty", "EMPTY_MESSAGE")

    if len(message) > MAX_MESSAGE_LENGTH:
        raise ValidationError(
            f"Message must be {MAX_MESSAGE_LENGTH} chars or less",
            "MESSAGE_TOO_LONG",
        )

    if not username:
        raise ValidationError("'username' is required", "MISSING_USERNAME")

    if not team:
        raise ValidationError("'team' is required", "MISSING_TEAM")

    return {
        "username": username,
        "team": team,
        "message": message,
    }


def filter_profanity(text: str) -> str:
    """
    Replace profane words with asterisks.

    Returns filtered text.
    """

    def mask(match):
        word = match.group()
        return word[0] + "*" * (len(word) - 1)

    return PROFANITY_PATTERN.sub(mask, text)
