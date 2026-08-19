from fastapi.testclient import TestClient

from main import MAX_UPLOAD_BYTES, app


client = TestClient(app)


def test_rejects_empty_file():
    response = client.post(
        "/analyze",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert response.status_code == 400


def test_rejects_unsupported_extension():
    response = client.post(
        "/analyze",
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 415


def test_rejects_corrupted_image():
    response = client.post(
        "/analyze",
        files={"file": ("broken.jpg", b"not a jpeg", "image/jpeg")},
    )
    assert response.status_code == 415


def test_rejects_oversized_upload():
    response = client.post(
        "/analyze",
        files={
            "file": (
                "large.png",
                b"0" * (MAX_UPLOAD_BYTES + 1),
                "image/png",
            )
        },
    )
    assert response.status_code == 413


def test_responses_include_security_and_observability_headers():
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-request-id"]
    assert float(response.headers["x-process-time-ms"]) >= 0
    csp = response.headers["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "unsafe-inline" not in csp
    assert "fonts.googleapis.com" not in csp


def test_nih_manifest_endpoint_reports_availability():
    response = client.get("/api/nih-manifest")
    assert response.status_code == 200
    payload = response.json()
    assert "available" in payload
    assert "download_command" in payload
    assert payload["download_command"] == "npm run download:nih-demo"


def test_cache_clear_requires_admin_token(monkeypatch):
    monkeypatch.setenv("THORAX_ADMIN_TOKEN", "secret-token")
    # Reload is not needed: ADMIN_TOKEN read at import. Patch module attribute.
    import main as main_module

    monkeypatch.setattr(main_module, "ADMIN_TOKEN", "secret-token")
    denied = client.post("/admin/cache/clear")
    assert denied.status_code == 401
    allowed = client.post(
        "/admin/cache/clear",
        headers={"X-Admin-Token": "secret-token"},
    )
    assert allowed.status_code == 200
    assert "cleared" in allowed.json()


def test_job_cancel_endpoint():
    response = client.post("/jobs/does-not-exist/cancel")
    assert response.status_code == 404


def test_cors_does_not_allow_unknown_origin():
    response = client.options(
        "/health",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers
