"""
Limitador simples em memória por endereço de origem.

Proteção educacional contra flood acidental em demos locais.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from config import settings


class RateLimiter:
    def __init__(
        self,
        max_requests: int | None = None,
        window_seconds: int | None = None,
    ):
        self.max_requests = (
            max_requests if max_requests is not None else settings.rate_limit_max
        )
        self.window_seconds = (
            window_seconds
            if window_seconds is not None
            else settings.rate_limit_window_seconds
        )
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self.allowed_total = 0
        self.rejected_total = 0

    def _purge_bucket_locked(self, bucket: deque[float], now: float) -> None:
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()

    def allow(self, key: str) -> tuple[bool, int]:
        """Retorna (permitido, retry_after_seconds)."""
        now = time.time()
        with self._lock:
            bucket = self._hits[key]
            self._purge_bucket_locked(bucket, now)
            if len(bucket) >= self.max_requests:
                retry_after = int(self.window_seconds - (now - bucket[0])) + 1
                self.rejected_total += 1
                return False, max(1, retry_after)
            bucket.append(now)
            self.allowed_total += 1
            return True, 0

    def stats(self) -> dict:
        now = time.time()
        with self._lock:
            for key in list(self._hits):
                bucket = self._hits[key]
                self._purge_bucket_locked(bucket, now)
                if not bucket:
                    del self._hits[key]
            active_hits = sum(len(bucket) for bucket in self._hits.values())
            return {
                "max_requests": self.max_requests,
                "window_seconds": self.window_seconds,
                "active_clients": len(self._hits),
                "active_hits": active_hits,
                "allowed_total": self.allowed_total,
                "rejected_total": self.rejected_total,
            }


def client_key(request, trust_proxy: bool | None = None) -> str:
    """Resolve a chave do cliente, opcionalmente via X-Forwarded-For."""
    if trust_proxy is None:
        trust_proxy = settings.trust_proxy
    if trust_proxy:
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"


RATE_LIMITED_PATHS = ("/analyze", "/compare")


def is_rate_limited_path(path: str) -> bool:
    return path == "/compare" or path.startswith("/analyze")


limiter = RateLimiter()
