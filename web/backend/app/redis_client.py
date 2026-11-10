"""Redis client for ephemeral data (pairing codes, WebSocket connections)."""

from __future__ import annotations

import json
import os
from typing import Any

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


class RedisClient:
    """Thin wrapper around Redis with fallback to in-memory store."""

    def __init__(self, url: str = REDIS_URL) -> None:
        self.url = url
        self._client: Any = None
        self._memory_store: dict[str, tuple[str, int]] = {}
        
        if REDIS_AVAILABLE:
            try:
                self._client = redis.from_url(url, decode_responses=True)
                self._client.ping()
            except Exception:
                self._client = None
    
    def set(self, key: str, value: str, ex: int | None = None) -> None:
        """Set key with optional expiry in seconds."""
        if self._client:
            self._client.set(key, value, ex=ex)
        else:
            import time
            expires = int(time.time()) + ex if ex else 0
            self._memory_store[key] = (value, expires)
    
    def get(self, key: str) -> str | None:
        """Get key value."""
        if self._client:
            return self._client.get(key)
        else:
            import time
            if key not in self._memory_store:
                return None
            value, expires = self._memory_store[key]
            if expires and time.time() > expires:
                del self._memory_store[key]
                return None
            return value
    
    def delete(self, key: str) -> None:
        """Delete key."""
        if self._client:
            self._client.delete(key)
        else:
            self._memory_store.pop(key, None)
    
    def setex(self, key: str, seconds: int, value: str) -> None:
        """Set key with expiry."""
        self.set(key, value, ex=seconds)
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        if self._client:
            return bool(self._client.exists(key))
        else:
            import time
            if key not in self._memory_store:
                return False
            _, expires = self._memory_store[key]
            if expires and time.time() > expires:
                del self._memory_store[key]
                return False
            return True


_redis_client: RedisClient | None = None


def get_redis() -> RedisClient:
    """Get singleton Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client


# Pairing code helpers

def store_pairing_code(code: str, data: dict[str, Any], ttl_seconds: int = 300) -> None:
    """Store pairing code with 5-minute TTL."""
    redis = get_redis()
    key = f"pairing:{code}"
    redis.setex(key, ttl_seconds, json.dumps(data))


def get_pairing_code(code: str) -> dict[str, Any] | None:
    """Retrieve and delete pairing code."""
    redis = get_redis()
    key = f"pairing:{code}"
    data = redis.get(key)
    if data:
        redis.delete(key)
        return json.loads(data)
    return None
