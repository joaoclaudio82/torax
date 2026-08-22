import time

from analysis_cache import AnalysisCache


def test_cache_hit_and_miss():
    cache = AnalysisCache(max_entries=2, ttl_seconds=60)
    key = cache.fingerprint(b"abc", "a.png")
    assert cache.get(key) is None
    cache.set(key, {"ok": True})
    assert cache.get(key) == {"ok": True}
    stats = cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_ratio"] == 0.5
    assert "approx_bytes" in stats


def test_cache_evicts_oldest_entries():
    cache = AnalysisCache(max_entries=2, ttl_seconds=60)
    cache.set("a", {"n": 1})
    cache.set("b", {"n": 2})
    cache.set("c", {"n": 3})
    assert cache.get("a") is None
    assert cache.get("b") == {"n": 2}
    assert cache.get("c") == {"n": 3}
    assert cache.stats()["evictions"] == 1


def test_cache_clear_resets_entries():
    cache = AnalysisCache(max_entries=2, ttl_seconds=60)
    cache.set("a", {"n": 1})
    removed = cache.clear()
    assert removed == 1
    assert cache.get("a") is None
    assert cache.stats()["entries"] == 0


def test_cache_counts_expired_entries():
    cache = AnalysisCache(max_entries=2, ttl_seconds=0)
    cache.set("a", {"n": 1})
    time.sleep(0.001)
    assert cache.get("a") is None
    assert cache.stats()["expirations"] == 1
