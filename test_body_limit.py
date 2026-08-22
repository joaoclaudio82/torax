from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from body_limit import RequestBodyLimitMiddleware, request_body_limit


def _client(max_upload_bytes=8):
    inner = FastAPI()

    @inner.post("/analyze")
    async def analyze(request: Request):
        return {"size": len(await request.body())}

    @inner.post("/other")
    async def other(request: Request):
        return {"size": len(await request.body())}

    app = RequestBodyLimitMiddleware(inner, max_upload_bytes=max_upload_bytes)
    return TestClient(app)


def test_request_body_limit_accounts_for_compare_pair():
    assert request_body_limit("/compare", 10) > request_body_limit("/analyze", 10)
    assert request_body_limit("/health", 10) is None


def test_small_analyze_body_reaches_application():
    client = _client()
    response = client.post("/analyze", content=b"1234")
    assert response.status_code == 200
    assert response.json()["size"] == 4


def test_content_length_guard_rejects_oversized_body():
    client = _client(max_upload_bytes=1)
    response = client.post("/analyze", content=b"x" * (2 * 1024 * 1024 + 2))
    assert response.status_code == 413
    assert "max_request_bytes" in response.json()
    assert response.headers["x-request-id"]


def test_unlimited_path_is_not_blocked_by_upload_policy():
    client = _client(max_upload_bytes=1)
    response = client.post("/other", content=b"x" * 1024)
    assert response.status_code == 200
