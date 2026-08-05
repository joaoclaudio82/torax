"""
API de triagem de radiografia de torax.

AVISO: ferramenta de pesquisa e ensino. Nao e dispositivo medico, nao possui
registro em ANVISA/FDA e nao deve ser usada para diagnostico ou decisao
clinica sobre pacientes reais.
"""
from __future__ import annotations

import io
import logging
import os
import time
import uuid

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import imaging
import overlay
import xray_model
from comparison import build_prediction_deltas
from radiograph_quality import assess_radiograph_quality

app = FastAPI(title="Triagem de Torax (prototipo de pesquisa)", version="2.0")
logger = logging.getLogger("thorax.api")
ALLOWED_ORIGINS = os.getenv(
    "THORAX_ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Request-ID"],
)

PROJECT_DIR = os.path.dirname(__file__)
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".dcm", ".dicom")
SUPPORTED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "application/dicom",
    "application/octet-stream",
}


@app.middleware("http")
async def security_and_observability(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; "
        "script-src 'self'; connect-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com"
    )
    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


def _has_valid_signature(data: bytes, filename: str) -> bool:
    name = filename.lower()
    if name.endswith(".png"):
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if name.endswith((".jpg", ".jpeg")):
        return data.startswith(b"\xff\xd8\xff")
    if name.endswith((".dcm", ".dicom")):
        if len(data) > 132 and data[128:132] == b"DICM":
            return True
        try:
            import pydicom

            dataset = pydicom.dcmread(
                io.BytesIO(data),
                force=True,
                stop_before_pixels=True,
            )
            return bool(getattr(dataset, "Rows", 0) and getattr(dataset, "Columns", 0))
        except Exception:  # noqa: BLE001
            return False
    return False


def _validate_upload(file: UploadFile, data: bytes) -> None:
    filename = (file.filename or "").lower()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Arquivo excede o limite de 15 MB.",
        )
    if not filename.endswith(SUPPORTED_EXTENSIONS):
        raise HTTPException(
            status_code=415,
            detail="Formato não suportado. Envie PNG, JPG ou DICOM.",
        )
    if file.content_type and file.content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Tipo de conteúdo não suportado.",
        )
    if not _has_valid_signature(data, filename):
        raise HTTPException(
            status_code=415,
            detail="A assinatura do arquivo não corresponde ao formato informado.",
        )


def _analyze_for_comparison(data: bytes, filename: str) -> dict:
    raw, metadata = imaging.load_image_with_metadata(data, filename)
    quality = imaging.assess_quality(raw)
    tensor, visible = imaging.preprocess(raw)
    probabilities = xray_model.predict(tensor)
    return {
        "probabilities": probabilities,
        "image": overlay.gray_to_b64(visible),
        "quality": quality,
        "metadata": metadata,
    }


@app.get("/health")
def health():
    m = xray_model.get_model()
    return {
        "status": "ok",
        "api_version": app.version,
        "weights": xray_model.WEIGHTS,
        "pathologies": len([p for p in m.pathologies if p]),
        "max_upload_mb": MAX_UPLOAD_BYTES // (1024 * 1024),
    }


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    target_pathology: str | None = Form(default=None),
):
    request_started = time.perf_counter()
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")
    _validate_upload(file, data)

    preprocessing_started = time.perf_counter()
    try:
        raw, image_metadata = imaging.load_image_with_metadata(
            data, file.filename or ""
        )
        input_quality = imaging.assess_quality(raw)
        radiograph_qc = assess_radiograph_quality(raw)
        tensor, vis_u8 = imaging.preprocess(raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422,
                            detail=f"Falha ao ler a imagem: {exc}")
    preprocessing_ms = (time.perf_counter() - preprocessing_started) * 1000

    inference_started = time.perf_counter()
    probs = xray_model.predict(tensor)
    inference_ms = (time.perf_counter() - inference_started) * 1000
    if target_pathology and target_pathology not in probs:
        raise HTTPException(
            status_code=422,
            detail=f"Patologia-alvo desconhecida: {target_pathology}.",
        )
    target = target_pathology or xray_model.top_target(probs)
    gradcam_started = time.perf_counter()
    cam = xray_model.gradcam(tensor, target)
    gradcam_ms = (time.perf_counter() - gradcam_started) * 1000

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
                "threshold_margin": (
                    round(v["threshold_margin"], 4)
                    if v["threshold_margin"] is not None else None
                ),
                "threshold_band": v["threshold_band"],
                "ambiguity": v["ambiguity"],
                "in_pneumonia_group": name in xray_model.PNEUMONIA_GROUP,
            }
            for name, v in ranked
        ],
        "image_original": overlay.gray_to_b64(vis_u8),
        "image_overlay": overlay.make_overlay(vis_u8, cam),
        "input_quality": input_quality,
        "radiograph_quality": radiograph_qc,
        "image_metadata": image_metadata,
        "decision_context": xray_model.decision_context(probs),
        "explainability": {
            "target_pathology": target,
            "cam_stats": xray_model.cam_stats(cam),
            "note": (
                "O mapa representa atenção do modelo e não delimita uma lesão."
            ),
        },
        "timings": {
            "preprocessing_ms": round(preprocessing_ms, 2),
            "inference_ms": round(inference_ms, 2),
            "gradcam_ms": round(gradcam_ms, 2),
            "total_ms": round((time.perf_counter() - request_started) * 1000, 2),
        },
        "disclaimer": (
            "Prototipo de pesquisa e ensino. Nao substitui avaliacao medica "
            "nem laudo radiologico. Nao usar em decisao clinica real."
        ),
    }


@app.post("/compare")
async def compare(
    file_a: UploadFile = File(...),
    file_b: UploadFile = File(...),
):
    request_started = time.perf_counter()
    data_a, data_b = await file_a.read(), await file_b.read()
    if not data_a or not data_b:
        raise HTTPException(status_code=400, detail="As duas imagens são obrigatórias.")
    _validate_upload(file_a, data_a)
    _validate_upload(file_b, data_b)

    try:
        analysis_a = _analyze_for_comparison(data_a, file_a.filename or "")
        analysis_b = _analyze_for_comparison(data_b, file_b.filename or "")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=422,
            detail=f"Falha ao comparar as imagens: {exc}",
        ) from exc

    deltas = build_prediction_deltas(
        analysis_a["probabilities"],
        analysis_b["probabilities"],
    )
    return {
        "image_a": analysis_a["image"],
        "image_b": analysis_b["image"],
        "quality_a": analysis_a["quality"],
        "quality_b": analysis_b["quality"],
        "metadata_a": analysis_a["metadata"],
        "metadata_b": analysis_b["metadata"],
        "deltas": deltas,
        "top_changes": deltas[:8],
        "timings": {
            "total_ms": round((time.perf_counter() - request_started) * 1000, 2),
        },
        "disclaimer": (
            "As diferenças refletem respostas estatísticas do modelo e não "
            "representam evolução clínica."
        ),
    }


@app.get("/")
def index():
    return FileResponse(os.path.join(PROJECT_DIR, "index.html"))


app.mount("/assets", StaticFiles(directory=os.path.join(PROJECT_DIR, "assets")), name="assets")


@app.get("/{filename:path}")
def frontend_file(filename: str):
    """Serve os arquivos estáticos do protótipo sem expor arquivos Python."""
    allowed = {"app.js", "data.js", "history.js", "styles.css", "viewer.js"}
    if filename not in allowed:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    return FileResponse(os.path.join(PROJECT_DIR, filename))
