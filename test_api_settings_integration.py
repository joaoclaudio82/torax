from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

import main


def _request(headers=None):
    raw_headers = []
    for key, value in (headers or {}).items():
        raw_headers.append((key.lower().encode(), value.encode()))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/health",
        "headers": raw_headers,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
        "query_string": b"",
        "http_version": "1.1",
    }
    return Request(scope)


def test_request_id_is_sanitized_and_bounded():
    value = "abc\nmalicious" + ("x" * 500)
    request_id = main._request_id(_request({"X-Request-ID": value}))
    assert "\n" not in request_id
    assert "\r" not in request_id
    assert len(request_id) <= main.settings.request_id_max_length


def test_request_id_falls_back_to_uuid_for_blank_header():
    request_id = main._request_id(_request({"X-Request-ID": "   "}))
    assert request_id
    assert len(request_id) <= main.settings.request_id_max_length


def test_upload_limit_uses_central_settings(monkeypatch):
    fake_settings = SimpleNamespace(max_upload_bytes=4, max_upload_mb=1)
    monkeypatch.setattr(main, "settings", fake_settings)
    upload = SimpleNamespace(filename="image.png", content_type="image/png")

    with pytest.raises(HTTPException) as exc:
        main._validate_upload(upload, b"12345")

    assert exc.value.status_code == 413
    assert "1 MB" in exc.value.detail


def test_public_runtime_config_does_not_expose_admin_token():
    payload = main.settings.public_dict()
    assert "admin_token" not in payload
