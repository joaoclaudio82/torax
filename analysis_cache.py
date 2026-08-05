"""
Cache em memória de resultados de análise por hash do arquivo.

Evita reprocessar o mesmo upload durante a sessão do servidor.
"""
from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict


class AnalysisCache:
    def __init__(self, max_entries: int = 32, ttl_seconds: int = 1800):
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._items: OrderedDict[str, tuple[float, dict]] = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    @staticmethod
    def fingerprint(data: bytes, filename: str, extras: str = "") -> str:
        digest = hashlib.sha256()
        digest.update(data)
        digest.update(b"\0")
        digest.update(filename.encode("utf-8", errors="ignore"))
        digest.update(b"\0")
        digest.update(extras.encode("utf-8", errors="ignore"))
        return digest.hexdigest()

    def get(self, key: str) -> dict | None:
        now = time.time()
        with self._lock:
            item = self._items.get(key)
            if item is None:
                self.misses += 1
                return None
            created, payload = item
            if now - created > self.ttl_seconds:
                del self._items[key]
                self.misses += 1
                return None
            self._items.move_to_end(key)
            self.hits += 1
            return payload

    def set(self, key: str, payload: dict) -> None:
        with self._lock:
            self._items[key] = (time.time(), payload)
            self._items.move_to_end(key)
            while len(self._items) > self.max_entries:
                self._items.popitem(last=False)

    def stats(self) -> dict:
        with self._lock:
            return {
                "entries": len(self._items),
                "max_entries": self.max_entries,
                "ttl_seconds": self.ttl_seconds,
                "hits": self.hits,
                "misses": self.misses,
            }


cache = AnalysisCache()
