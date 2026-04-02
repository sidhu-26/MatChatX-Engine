"""
WebSocket Chat Consumer

Handles real-time match chat via Django Channels.

Flow:
  1. User connects to ws://host/ws/chat/<match_id>/
  2. User sends join payload with username + team
  3. User receives last 15 messages from Redis
  4. User can send/receive messages in real-time
  5. All data auto-expires after match ends
"""

import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from matches.models import Match, MatchStatus
from matches.services import get_match_by_id, get_match_ttl_seconds

from .services import (
    add_message,
    get_last_messages,
    publish_message,
    check_rate_limit,
)
from .validators import (
    validate_message_payload,
    filter_profanity,
    ValidationError,
)

logger = logging.getLogger("chat")


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Async WebSocket consumer for match chat rooms.

    Each match has a channel group: match_<uuid>
    Messages are stored in Redis (not PostgreSQL).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.match_id = None
        self.room_group_name = None
        self.username = None
        self.team = None
        self.match = None
        self.joined = False

    async def connect(self):
        """
        Handle WebSocket connection.

        Validates the match exists and is LIVE before accepting.
        """
        self.match_id = self.scope["url_route"]["kwargs"]["match_id"]
        self.room_group_name = f"match_{self.match_id}"

        logger.info(f"[CONNECT] Attempting connection to match={self.match_id}")

        # Validate match exists and is LIVE
        self.match = await database_sync_to_async(get_match_by_id)(self.match_id)

        if self.match is None:
            logger.warning(f"[CONNECT] Match not found: {self.match_id}")
            await self.close(code=4004)
            return

        if not self.match.is_live:
            logger.warning(
                f"[CONNECT] Match not LIVE: {self.match_id} "
                f"(status={self.match.status})"
            )
            await self.close(code=4003)
            return

        # Join the channel group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        logger.info(f"[CONNECT] Connected to match={self.match_id}")

        # Prompt user to send join payload
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": "Connected! Send your join payload with username and team_supported.",
            "match": {
                "id": str(self.match.id),
                "team_1": self.match.team_1,
                "team_2": self.match.team_2,
                "status": self.match.status,
            },
        }))

    async def disconnect(self, close_code):
        """Handle clean disconnection."""
        if self.room_group_name:
            # Leave the channel group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

            # Notify room about user leaving
            if self.username:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "user_event",
                        "event": "leave",
                        "username": self.username,
                        "team": self.team or "",
                    },
                )

                logger.info(
                    f"[DISCONNECT] user={self.username} match={self.match_id} "
                    f"code={close_code}"
                )

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handle incoming WebSocket messages.

        Two message types:
        1. Join payload (first message): {"username": "...", "team_supported": "..."}
        2. Chat message: {"username": "...", "team": "...", "message": "..."}
        """
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            await self._send_error("Invalid JSON payload", "INVALID_JSON")
            return

        # Handle join payload (first message after connect)
        if not self.joined:
            await self._handle_join(data)
            return

        # Handle chat message
        await self._handle_message(data)

    async def _handle_join(self, data: dict):
        """Process user join payload and send chat history."""
        username = data.get("username", "").strip()
        team_supported = data.get("team_supported", "").strip()

        if not username:
            await self._send_error("'username' is required", "MISSING_USERNAME")
            return

        if not team_supported:
            await self._send_error(
                "'team_supported' is required", "MISSING_TEAM"
            )
            return

        self.username = username
        self.team = team_supported
        self.joined = True

        logger.info(
            f"[JOIN] user={self.username} team={self.team} "
            f"match={self.match_id}"
        )

        # Send chat history (last 15 messages)
        history = await get_last_messages(str(self.match_id))

        await self.send(text_data=json.dumps({
            "type": "chat_history",
            "messages": history,
            "count": len(history),
        }))

        # Notify room about new user
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_event",
                "event": "join",
                "username": self.username,
                "team": self.team,
            },
        )

    async def _handle_message(self, data: dict):
        """Process and broadcast a chat message."""
        # Re-validate match is still LIVE
        self.match = await database_sync_to_async(get_match_by_id)(
            str(self.match_id)
        )

        if self.match is None or not self.match.is_live:
            await self._send_error(
                "Match is no longer live. Chat is closed.",
                "MATCH_CLOSED",
            )
            await self.close(code=4003)
            return

        # Validate message payload
        try:
            validated = validate_message_payload(data)
        except ValidationError as e:
            await self._send_error(e.message, e.code)
            return

        # Rate limiting
        allowed = await check_rate_limit(str(self.match_id), self.username)
        if not allowed:
            await self._send_error(
                "You're sending messages too fast. Please slow down.",
                "RATE_LIMITED",
            )
            return

        # Apply profanity filter
        validated["message"] = filter_profanity(validated["message"])

        # Calculate TTL for Redis storage
        ttl = await database_sync_to_async(get_match_ttl_seconds)(self.match)

        # Store in Redis
        msg_data = await add_message(
            match_id=str(self.match_id),
            username=validated["username"],
            team=validated["team"],
            message=validated["message"],
            ttl_seconds=ttl,
        )

        # Publish via Redis Pub/Sub (for cross-process)
        await publish_message(str(self.match_id), msg_data)

        # Broadcast to WebSocket group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": msg_data,
            },
        )

    # ─── Channel Layer Event Handlers ────────────────────────────────

    async def chat_message(self, event):
        """Handle chat.message event from channel layer."""
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            **event["message"],
        }))

    async def user_event(self, event):
        """Handle user join/leave events."""
        await self.send(text_data=json.dumps({
            "type": "user_event",
            "event": event["event"],
            "username": event["username"],
            "team": event["team"],
        }))

    # ─── Helpers ─────────────────────────────────────────────────────

    async def _send_error(self, message: str, code: str):
        """Send an error message to the client."""
        await self.send(text_data=json.dumps({
            "type": "error",
            "code": code,
            "message": message,
        }))
        logger.warning(
            f"[ERROR] code={code} user={self.username} "
            f"match={self.match_id}: {message}"
        )
