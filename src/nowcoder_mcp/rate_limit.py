from __future__ import annotations

import time
from collections import deque

from .errors import RateLimitedError


class SlidingWindowRateLimiter:
    def __init__(self, limit_per_minute: int = 30):
        self.limit = max(1, limit_per_minute)
        self.window_seconds = 60.0
        self._events: deque[float] = deque()

    def check(self) -> None:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        while self._events and self._events[0] < cutoff:
            self._events.popleft()
        if len(self._events) >= self.limit:
            raise RateLimitedError(
                f"Nowcoder request rate limit exceeded ({self.limit}/minute). Retry later."
            )
        self._events.append(now)
