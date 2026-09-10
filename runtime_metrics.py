"""Métricas operacionais leves, em memória e sem dados de paciente."""
from __future__ import annotations

from collections import Counter, deque
import math
import threading
import time


class RuntimeMetrics:
    def __init__(self, latency_sample_size: int = 512) -> None:
        self.started_at = time.time()
        self._lock = threading.Lock()
        self._requests = 0
        self._duration_ms = 0.0
        self._status_codes: Counter[str] = Counter()
        self._paths: Counter[str] = Counter()
        self._rate_limited = 0
        self._upload_rejections = 0
        self._latencies_ms: deque[float] = deque(maxlen=max(16, latency_sample_size))

    @staticmethod
    def _percentile(values: list[float], percentile: float) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        rank = (len(ordered) - 1) * percentile
        lower = math.floor(rank)
        upper = math.ceil(rank)
        if lower == upper:
            return ordered[lower]
        weight = rank - lower
        return ordered[lower] * (1.0 - weight) + ordered[upper] * weight

    def record_request(self, path: str, status_code: int, duration_ms: float) -> None:
        normalized_duration = max(0.0, float(duration_ms))
        with self._lock:
            self._requests += 1
            self._duration_ms += normalized_duration
            self._latencies_ms.append(normalized_duration)
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
            latencies = list(self._latencies_ms)
            return {
                "uptime_seconds": round(max(0.0, time.time() - self.started_at), 3),
                "requests_total": self._requests,
                "request_duration_ms_total": round(self._duration_ms, 3),
                "request_duration_ms_avg": round(avg, 3),
                "request_duration_ms_p50": round(self._percentile(latencies, 0.50), 3),
                "request_duration_ms_p95": round(self._percentile(latencies, 0.95), 3),
                "latency_sample_size": len(latencies),
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
            self._latencies_ms.clear()
            self._status_codes.clear()
            self._paths.clear()
            self._rate_limited = 0
            self._upload_rejections = 0


metrics = RuntimeMetrics()
