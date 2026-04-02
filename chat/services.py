"""
Redis Service Layer for Chat

All chat message storage and retrieval happens through Redis.
No PostgreSQL for messages — ever.

Key patterns:
  - match_{id}_messages  → LIST (last N messages, LPUSH + LTRIM)
  - rate_{match_id}_{username} → rate limit counter

TTL:
  - All keys expire at match.end_time + 30 minutes
"""

import json
import logging
from datetime import datetime, timezone as tz

import redis.asyncio as aioredis
from django.conf import settings

logger = logging.getLogger("chat")

# Async Redis connection pool (singleton)
_redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get or create async Redis connection."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            max_connections=50,
        )
    return _redis_pool


def _messages_key(match_id: str) -> str:
    """Redis key for match messages list."""
    return f"match_{match_id}_messages"


def _rate_key(match_id: str, username: str) -> str:
    """Redis key for rate limiting a user in a match."""
    return f"rate_{match_id}_{username}"


async def add_message(
    match_id: str,
    username: str,
    team: str,
    message: str,
    ttl_seconds: int,
) -> dict:
    """
    Store a message in Redis.

    Uses LPUSH + LTRIM to maintain a sliding window of the last N messages.
    Sets TTL on the key so data auto-expires after match ends.

    Returns the full message dict with timestamp.
    """
    r = await get_redis()
    max_messages = settings.CHAT_MAX_MESSAGES
    key = _messages_key(match_id)

    timestamp = datetime.now(tz.utc).isoformat()

    msg_data = {
        "username": username,
        "team": team,
        "message": message,
        "timestamp": timestamp,
    }

    msg_json = json.dumps(msg_data, ensure_ascii=False)

    # Atomic: push + trim + set expiry
    pipe = r.pipeline()
    pipe.lpush(key, msg_json)
    pipe.ltrim(key, 0, max_messages - 1)
    pipe.expire(key, ttl_seconds)
    await pipe.execute()

    logger.info(
        f"[STORE] match={match_id} user={username} team={team} "
        f"msg_len={len(message)}"
    )

    return msg_data


async def get_last_messages(match_id: str) -> list[dict]:
    """
    Retrieve the last N messages for a match from Redis.

    Returns messages in chronological order (oldest first).
    """
    r = await get_redis()
    key = _messages_key(match_id)
    max_messages = settings.CHAT_MAX_MESSAGES

    raw_messages = await r.lrange(key, 0, max_messages - 1)

    # Redis LPUSH stores newest first, reverse for chronological order
    messages = []
    for raw in reversed(raw_messages):
        try:
            messages.append(json.loads(raw))
        except json.JSONDecodeError:
            logger.warning(f"Corrupt message in {key}: {raw[:50]}")
            continue

    return messages


async def publish_message(match_id: str, message_data: dict) -> None:
    """
    Publish message via Redis Pub/Sub for cross-process broadcasting.
    """
    r = await get_redis()
    channel = f"match_{match_id}"
    await r.publish(channel, json.dumps(message_data, ensure_ascii=False))


async def check_rate_limit(match_id: str, username: str) -> bool:
    """
    Check if user has exceeded rate limit.

    Returns True if the user is ALLOWED to send.
    Returns False if rate-limited.

    Uses a sliding window counter with TTL.
    """
    r = await get_redis()
    key = _rate_key(match_id, username)
    limit = settings.RATE_LIMIT_MESSAGES
    window = settings.RATE_LIMIT_WINDOW_SECONDS

    current = await r.get(key)

    if current is None:
        # First message in window
        pipe = r.pipeline()
        pipe.set(key, 1, ex=window)
        await pipe.execute()
        return True

    if int(current) >= limit:
        logger.warning(
            f"[RATE_LIMIT] match={match_id} user={username} "
            f"count={current}/{limit}"
        )
        return False

    await r.incr(key)
    return True


async def cleanup_match_data(match_id: str) -> None:
    """
    Explicitly clean up Redis data for a match.
    Called when match transitions to CLOSED (backup to TTL).
    """
    r = await get_redis()
    key = _messages_key(match_id)

    deleted = await r.delete(key)
    if deleted:
        logger.info(f"[CLEANUP] Deleted messages for match={match_id}")
