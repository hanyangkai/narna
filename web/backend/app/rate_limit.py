"""Rate limiting — Redis when UAP_REDIS_URL is set (multi-replica safe), else memory."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse


class RateLimiter(Protocol):
    def allow(self, key: str) -> tuple[bool, float]: ...


@dataclass
class _Bucket:
    window_start: float
    used: int


class InMemoryRateLimiter:
    def __init__(self, *, limit_per_min: int = 120) -> None:
        self.limit_per_min = limit_per_min
        self.window_seconds = 60.0
        self._buckets: dict[str, _Bucket] = {}

    def _bucket(self, key: str) -> _Bucket:
        now = time.time()
        b = self._buckets.get(key)
        if b is None or (now - b.window_start) >= self.window_seconds:
            b = _Bucket(window_start=now, used=0)
            self._buckets[key] = b
        return b

    def allow(self, key: str) -> tuple[bool, float]:
        b = self._bucket(key)
        if b.used >= self.limit_per_min:
            now = time.time()
            retry = max(0.0, (b.window_start + self.window_seconds) - now)
            return False, retry
        b.used += 1
        return True, 0.0


class RedisRateLimiter:
    """Fixed-window counter via Redis INCR + EXPIRE (shared across API replicas)."""

    def __init__(self, *, url: str, limit_per_min: int = 120) -> None:
        self.limit_per_min = limit_per_min
        self.window_seconds = 60
        self._url = url
        self._client = None

    def _conn(self):
        if self._client is not None:
            return self._client
        # Prefer redis-py if installed; else raw TCP RESP for INCR/EXPIRE/TTL
        try:
            import redis  # type: ignore

            self._client = redis.Redis.from_url(self._url, decode_responses=True, socket_timeout=1.5)
            self._client.ping()
            self._mode = "redis-py"
            return self._client
        except Exception:
            self._mode = "raw"
            return None

    def allow(self, key: str) -> tuple[bool, float]:
        try:
            client = self._conn()
            rkey = f"narna:rl:{key}"
            if client is not None and getattr(self, "_mode", "") == "redis-py":
                n = int(client.incr(rkey))
                if n == 1:
                    client.expire(rkey, self.window_seconds)
                if n > self.limit_per_min:
                    ttl = client.ttl(rkey)
                    return False, float(ttl if ttl and ttl > 0 else self.window_seconds)
                return True, 0.0
            return self._raw_allow(rkey)
        except Exception:
            # Fail open to local memory for this key on Redis blip
            return InMemoryRateLimiter(limit_per_min=self.limit_per_min).allow(key)

    def _raw_allow(self, rkey: str) -> tuple[bool, float]:
        """Minimal RESP without redis-py dependency."""
        u = urlparse(self._url)
        host = u.hostname or "127.0.0.1"
        port = int(u.port or 6379)
        import socket

        def cmd(sock: socket.socket, parts: list[str]) -> bytes:
            buf = f"*{len(parts)}\r\n".encode()
            for p in parts:
                b = p.encode()
                buf += f"${len(b)}\r\n".encode() + b + b"\r\n"
            sock.sendall(buf)
            return sock.recv(4096)

        with socket.create_connection((host, port), timeout=1.5) as sock:
            # INCR
            resp = cmd(sock, ["INCR", rkey]).decode("utf-8", errors="replace")
            # :N\r\n
            n = 0
            for line in resp.split("\r\n"):
                if line.startswith(":"):
                    n = int(line[1:] or "0")
                    break
            if n == 1:
                cmd(sock, ["EXPIRE", rkey, str(self.window_seconds)])
            if n > self.limit_per_min:
                ttl_resp = cmd(sock, ["TTL", rkey]).decode("utf-8", errors="replace")
                ttl = self.window_seconds
                for line in ttl_resp.split("\r\n"):
                    if line.startswith(":"):
                        ttl = max(0, int(line[1:] or "0"))
                        break
                return False, float(ttl)
            return True, 0.0


def build_rate_limiter(*, limit_per_min: int = 120) -> RateLimiter:
    url = (os.environ.get("UAP_REDIS_URL") or "").strip()
    if url:
        try:
            return RedisRateLimiter(url=url, limit_per_min=limit_per_min)
        except Exception:
            pass
    return InMemoryRateLimiter(limit_per_min=limit_per_min)
