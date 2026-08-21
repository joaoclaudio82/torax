from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import operational_api
from operational_api import install_operational_features


class FakeModel:
    pathologies = ["Pneumonia", "Effusion"]
    op_threshs = [0.4, 0.5]


def _app(monkeypatch):
    app = FastAPI(version="9.9.9")

    @app.get("/{filename:path}")
    def fallback(filename: str):
        raise HTTPException(status_code=404, detail=f"fallback:{filename}")

    monkeypatch.setattr(operational_api.xray_model, "get_model", lambda: FakeModel())
    install_operational_features(app)
    return app


def test_operational_routes_are_reachable_before_frontend_fallback(monkeypatch):
    client = TestClient(_app(monkeypatch))
    live = client.get("/health/live")
    ready = client.get("/health/ready")
    assert live.status_code == 200
    assert live.json()["api_version"] == "9.9.9"
    assert ready.status_code == 200
    assert ready.json()["pathologies"] == 2


def test_public_config_does_not_expose_admin_token(monkeypatch):
    client = TestClient(_app(monkeypatch))
    payload = client.get("/api/config").json()
    assert "admin_token" not in payload


def test_model_card_is_available(monkeypatch):
    client = TestClient(_app(monkeypatch))
    payload = client.get("/api/model").json()
    assert payload["architecture"] == "DenseNet-121"
    assert payload["pathology_count"] == 2
    assert payload["clinical_use"] is False


def test_request_id_is_sanitized(monkeypatch):
    client = TestClient(_app(monkeypatch))
    response = client.get("/health/live", headers={"X-Request-ID": "safe-id-123"})
    assert response.headers["x-request-id"] == "safe-id-123"
