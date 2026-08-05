from rate_limit import RateLimiter


def test_rate_limiter_allows_until_window_is_full():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    assert limiter.allow("client-a")[0] is True
    assert limiter.allow("client-a")[0] is True
    allowed, retry_after = limiter.allow("client-a")
    assert allowed is False
    assert retry_after >= 1


def test_rate_limiter_isolates_clients():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    assert limiter.allow("a")[0] is True
    assert limiter.allow("b")[0] is True
