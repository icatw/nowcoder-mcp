from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_STATE_PATH = Path.home() / ".config" / "nowcoder-mcp" / "storage_state.json"


@dataclass(frozen=True)
class NowcoderConfig:
    auth_mode: str = "anonymous"
    auth_state_path: Path = DEFAULT_STATE_PATH
    cookie_env_name: str = "NOWCODER_COOKIE"
    timeout_seconds: float = 20.0
    max_pages_cap: int = 10
    rate_limit_per_minute: int = 30
    cache_ttl_seconds: int = 600

    @classmethod
    def from_env(cls) -> "NowcoderConfig":
        return cls(
            auth_mode=os.getenv("NOWCODER_AUTH_MODE", "anonymous"),
            auth_state_path=Path(os.getenv("NOWCODER_AUTH_STATE", str(DEFAULT_STATE_PATH))).expanduser(),
            cookie_env_name=os.getenv("NOWCODER_COOKIE_ENV", "NOWCODER_COOKIE"),
            timeout_seconds=float(os.getenv("NOWCODER_TIMEOUT_SECONDS", "20")),
            max_pages_cap=int(os.getenv("NOWCODER_MAX_PAGES_CAP", "10")),
            rate_limit_per_minute=int(os.getenv("NOWCODER_RATE_LIMIT_PER_MINUTE", "30")),
            cache_ttl_seconds=int(os.getenv("NOWCODER_CACHE_TTL_SECONDS", "600")),
        )
