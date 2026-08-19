from rate_limit import RateLimiter, client_key, is_rate_limited_path


class DummyRequest:
    def __init__(self, host="127.0.0.1", forwarded=None):
        self.client = type("Client", (), {"host": host})()
        self.headers = {}
        if forwarded is not None:
            self.headers["X-Forwarded-For"] = forwarded


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


def test_is_rate_limited_path_covers_compare_and_analyze():
    assert is_rate_limited_path("/compare") is True
    assert is_rate_limited_path("/analyze") is True
    assert is_rate_limited_path("/analyze/async") is True
    assert is_rate_limited_path("/health") is False


def test_client_key_uses_forwarded_only_when_trusted():
    request = DummyRequest(host="10.0.0.1", forwarded="203.0.113.9, 10.0.0.1")
    assert client_key(request, trust_proxy=False) == "10.0.0.1"
    assert client_key(request, trust_proxy=True) == "203.0.113.9"
