"""Teste de fumaça: gera uma imagem sintética em tons de cinza, chama o
endpoint /analyze e verifica o formato da resposta. Não valida acurácia
clínica; apenas confirma que o pipeline roda de ponta a ponta."""
import io

import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from entrypoint import app

client = TestClient(app)


def synthetic_xray(size=256):
    # Fundo escuro com dois "campos pulmonares" mais claros e ruído.
    img = np.random.normal(30, 8, (size, size)).clip(0, 255)
    yy, xx = np.mgrid[0:size, 0:size]
    for cx in (size * 0.32, size * 0.68):
        blob = np.exp(
            -(
                ((xx - cx) ** 2) / (2 * (size * 0.12) ** 2)
                + ((yy - size * 0.5) ** 2) / (2 * (size * 0.22) ** 2)
            )
        )
        img += blob * 120
    img = img.clip(0, 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    return buf.getvalue()


def test_liveness_and_readiness():
    live = client.get("/health/live")
    assert live.status_code == 200, live.text
    assert live.json()["status"] == "ok"

    ready = client.get("/health/ready")
    assert ready.status_code == 200, ready.text
    assert ready.json()["status"] == "ready"
    assert ready.json()["model_loaded"] is True


def test_analyze():
    png = synthetic_xray()
    r = client.post("/analyze", files={"file": ("synthetic.png", png, "image/png")})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "predictions" in data and len(data["predictions"]) >= 10
    assert data["image_overlay"].startswith("data:image/png;base64,")
    assert 0 <= data["input_quality"]["score"] <= 100
    assert "metrics" in data["input_quality"]
    assert data["image_metadata"]["format"] == "PNG"
    assert data["image_metadata"]["anonymized"] is True
    assert data["explainability"]["target_pathology"] == data["target_pathology"]
    assert "visual_region" in data["explainability"]["cam_stats"]
    assert "borderline_classes" in data["decision_context"]
    assert all("ambiguity" in prediction for prediction in data["predictions"])
    assert data["timings"]["total_ms"] >= data["timings"]["inference_ms"]
    assert r.headers["x-request-id"]
    assert data["target_pathology"] in [p["pathology"] for p in data["predictions"]]


def test_explicit_gradcam_target():
    png = synthetic_xray()
    r = client.post(
        "/analyze",
        data={"target_pathology": "Effusion"},
        files={"file": ("synthetic.png", png, "image/png")},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["target_pathology"] == "Effusion"
    assert data["explainability"]["target_pathology"] == "Effusion"


def test_operational_metrics_after_requests():
    response = client.get("/metrics")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["runtime"]["requests_total"] >= 1
    assert "cache" in payload
    assert "jobs" in payload
    assert "rate_limit" in payload


if __name__ == "__main__":
    test_liveness_and_readiness()
    test_analyze()
    test_explicit_gradcam_target()
    test_operational_metrics_after_requests()
    print("\nOK: pipeline completo executou.")
