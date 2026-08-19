"""
Limitador simples em memória por endereço de origem.

Proteção educacional contra flood acidental em demos locais.
"""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


class RateLimiter:
    def __init__(
        self,
        max_requests: int | None = None,
        window_seconds: int | None = None,
    ):
        self.max_requests = (
            max_requests
            if max_requests is not None
            else _env_int("THORAX_RATE_LIMIT_MAX", 30)
        )
        self.window_seconds = (
            window_seconds
            if window_seconds is not None
            else _env_int("THORAX_RATE_LIMIT_WINDOW", 60)
        )
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> tuple[bool, int]:
        """Retorna (permitido, retry_after_seconds)."""
        now = time.time()
        with self._lock:
            bucket = self._hits[key]
            while bucket and now - bucket[0] > self.window_seconds:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                retry_after = int(self.window_seconds - (now - bucket[0])) + 1
                return False, max(1, retry_after)
            bucket.append(now)
            return True, 0


def client_key(request, trust_proxy: bool | None = None) -> str:
    """Resolve a chave do cliente, opcionalmente via X-Forwarded-For."""
    if trust_proxy is None:
        trust_proxy = os.getenv("THORAX_TRUST_PROXY", "").lower() in {
            "1",
            "true",
            "yes",
        }
    if trust_proxy:
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"


RATE_LIMITED_PATHS = ("/analyze", "/compare")


def is_rate_limited_path(path: str) -> bool:
    return path == "/compare" or path.startswith("/analyze")


limiter = RateLimiter()
