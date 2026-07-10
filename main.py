"""
API de triagem de radiografia de torax.

AVISO: ferramenta de pesquisa e ensino. Nao e dispositivo medico, nao possui
registro em ANVISA/FDA e nao deve ser usada para diagnostico ou decisao
clinica sobre pacientes reais.
"""
from __future__ import annotations

import os

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import imaging
import overlay
import xray_model

app = FastAPI(title="Triagem de Torax (prototipo de pesquisa)", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_DIR = os.path.dirname(__file__)


@app.get("/health")
def health():
    m = xray_model.get_model()
    return {"status": "ok", "weights": xray_model.WEIGHTS,
            "pathologies": len([p for p in m.pathologies if p])}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")

    try:
        raw = imaging.load_image(data, file.filename or "")
        tensor, vis_u8 = imaging.preprocess(raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422,
                            detail=f"Falha ao ler a imagem: {exc}")

    probs = xray_model.predict(tensor)
    target = xray_model.top_target(probs)
    cam = xray_model.gradcam(tensor, target)

    ranked = sorted(probs.items(), key=lambda kv: kv[1]["prob"], reverse=True)

    return {
        "target_pathology": target,
        "pneumonia_group": xray_model.PNEUMONIA_GROUP,
        "predictions": [
            {
                "pathology": name,
                "prob": round(v["prob"], 4),
                "op_threshold": (round(v["op_threshold"], 4)
                                 if v["op_threshold"] is not None else None),
                "above_threshold": (
                    v["op_threshold"] is not None and v["prob"] >= v["op_threshold"]
                ),
                "in_pneumonia_group": name in xray_model.PNEUMONIA_GROUP,
            }
            for name, v in ranked
        ],
        "image_original": overlay.gray_to_b64(vis_u8),
        "image_overlay": overlay.make_overlay(vis_u8, cam),
        "disclaimer": (
            "Prototipo de pesquisa e ensino. Nao substitui avaliacao medica "
            "nem laudo radiologico. Nao usar em decisao clinica real."
        ),
    }


@app.get("/")
def index():
    return FileResponse(os.path.join(PROJECT_DIR, "index.html"))


app.mount("/assets", StaticFiles(directory=os.path.join(PROJECT_DIR, "assets")), name="assets")


@app.get("/{filename:path}")
def frontend_file(filename: str):
    """Serve os arquivos estáticos do protótipo sem expor arquivos Python."""
    allowed = {"app.js", "data.js", "styles.css"}
    if filename not in allowed:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    return FileResponse(os.path.join(PROJECT_DIR, filename))
