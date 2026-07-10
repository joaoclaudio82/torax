"""Teste de fumaca: gera uma imagem sintetica em tons de cinza, chama o
endpoint /analyze e verifica o formato da resposta. Nao valida acuracia
clinica; apenas confirma que o pipeline roda de ponta a ponta."""
import io
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def synthetic_xray(size=256):
    # Fundo escuro com dois "campos pulmonares" mais claros e ruido.
    img = np.random.normal(30, 8, (size, size)).clip(0, 255)
    yy, xx = np.mgrid[0:size, 0:size]
    for cx in (size * 0.32, size * 0.68):
        blob = np.exp(-(((xx - cx) ** 2) / (2 * (size * 0.12) ** 2)
                        + ((yy - size * 0.5) ** 2) / (2 * (size * 0.22) ** 2)))
        img += blob * 120
    img = img.clip(0, 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    return buf.getvalue()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ok"
    print("health ok:", r.json())


def test_analyze():
    png = synthetic_xray()
    r = client.post("/analyze", files={"file": ("synthetic.png", png, "image/png")})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "predictions" in data and len(data["predictions"]) >= 10
    assert data["image_overlay"].startswith("data:image/png;base64,")
    assert data["target_pathology"] in [p["pathology"] for p in data["predictions"]]
    top = data["predictions"][0]
    print("target:", data["target_pathology"])
    print("top-3:", [(p["pathology"], p["prob"]) for p in data["predictions"][:3]])
    print("overlay bytes:", len(data["image_overlay"]))


if __name__ == "__main__":
    test_health()
    test_analyze()
    print("\nOK: pipeline completo executou.")
