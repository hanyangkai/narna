from __future__ import annotations

import time
from dataclasses import dataclass


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

