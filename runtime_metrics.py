"""Métricas operacionais leves, em memória e sem dados de paciente."""
from __future__ import annotations

from collections import Counter
import threading
import time


class RuntimeMetrics:
    def __init__(self) -> None:
        self.started_at = time.time()
        self._lock = threading.Lock()
        self._requests = 0
        self._duration_ms = 0.0
        self._status_codes: Counter[str] = Counter()
        self._paths: Counter[str] = Counter()
        self._rate_limited = 0
        self._upload_rejections = 0

    def record_request(self, path: str, status_code: int, duration_ms: float) -> None:
        with self._lock:
            self._requests += 1
            self._duration_ms += max(0.0, float(duration_ms))
            self._status_codes[str(status_code)] += 1
            self._paths[path] += 1

    def record_rate_limited(self) -> None:
        with self._lock:
            self._rate_limited += 1

    def record_upload_rejection(self) -> None:
        with self._lock:
            self._upload_rejections += 1

    def snapshot(self) -> dict:
        with self._lock:
            avg = self._duration_ms / self._requests if self._requests else 0.0
            return {
                "uptime_seconds": round(max(0.0, time.time() - self.started_at), 3),
                "requests_total": self._requests,
                "request_duration_ms_total": round(self._duration_ms, 3),
                "request_duration_ms_avg": round(avg, 3),
                "status_codes": dict(self._status_codes),
                "paths": dict(self._paths),
                "rate_limited_total": self._rate_limited,
                "upload_rejections_total": self._upload_rejections,
            }

    def reset(self) -> None:
        with self._lock:
            self.started_at = time.time()
            self._requests = 0
            self._duration_ms = 0.0
            self._status_codes.clear()
            self._paths.clear()
            self._rate_limited = 0
            self._upload_rejections = 0


metrics = RuntimeMetrics()
