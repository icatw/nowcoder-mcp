from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self, ttl_seconds: int = 600):
        self.ttl_seconds = ttl_seconds
        self._items: dict[str, CacheEntry] = {}

    def get(self, key: str) -> Any | None:
        entry = self._items.get(key)
        if not entry:
            return None
        if entry.expires_at < time.monotonic():
            self._items.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: Any) -> None:
        self._items[key] = CacheEntry(value=value, expires_at=time.monotonic() + self.ttl_seconds)

    def clear(self) -> None:
        self._items.clear()
