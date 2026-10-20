import json
import logging

import redis

from app.config import settings

logger = logging.getLogger(__name__)

EVENTS_CHANNEL = "cloudpulse:events"

_client = redis.Redis.from_url(
    settings.redis_url, decode_responses=True, socket_connect_timeout=1, socket_timeout=1
)


def cache_get_json(key: str):
    try:
        raw = _client.get(key)
        return json.loads(raw) if raw else None
    except redis.RedisError:
        logger.warning("Redis unavailable; cache read skipped")
        return None


def cache_set_json(key: str, value, ttl_seconds: int) -> None:
    try:
        _client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
    except redis.RedisError:
        logger.warning("Redis unavailable; cache write skipped")


def publish_event(event: dict) -> None:
    try:
        _client.publish(EVENTS_CHANNEL, json.dumps(event, default=str))
    except redis.RedisError:
        logger.warning("Redis unavailable; live event not published")
