"""
API de triagem de radiografia de torax.

AVISO: ferramenta de pesquisa e ensino. Nao e dispositivo medico, nao possui
registro em ANVISA/FDA e nao deve ser usada para diagnostico ou decisao
clinica sobre pacientes reais.
"""
from __future__ import annotations

import io
import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import imaging
import overlay
import xray_model
from analysis_cache import cache as analysis_cache
from comparison import build_prediction_deltas
from jobs import run_job, store as job_store
from radiograph_quality import assess_radiograph_quality
from rate_limit import client_key, is_rate_limited_path, limiter as rate_limiter
from uncertainty import estimate_prediction_stability

app = FastAPI(title="Triagem de Torax (prototipo de pesquisa)", version="2.2.0")
logger = logging.getLogger("thorax.api")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "THORAX_ALLOWED_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if origin.strip()
]
ADMIN_TOKEN = os.getenv("THORAX_ADMIN_TOKEN", "").strip()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Request-ID", "X-Admin-Token"],
)

PROJECT_DIR = os.path.dirname(__file__)
NIH_DEMO_DIR = Path(PROJECT_DIR) / "assets" / "nih-demo"
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".dcm", ".dicom")
SUPPORTED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "application/dicom",
    "application/octet-stream",
}

# Cache intermediário: fingerprint do arquivo -> artefatos de inferência.
_inference_lock = threading.Lock()
_inference_cache: dict[str, dict] = {}


@app.middleware("http")
async def security_and_observability(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    if request.method == "POST" and is_rate_limited_path(request.url.path):
        key = client_key(request)
        allowed, retry_after = rate_limiter.allow(key)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Limite de requisições excedido. Tente novamente em breve."
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-Request-ID": request_id,
                },
            )
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
        "style-src 'self'; font-src 'self'"
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


def _predictions_payload(probs: dict) -> list[dict]:
    ranked = sorted(probs.items(), key=lambda kv: kv[1]["prob"], reverse=True)
    return [
        {
            "pathology": name,
            "prob": round(v["prob"], 4),
            "op_threshold": (
                round(v["op_threshold"], 4) if v["op_threshold"] is not None else None
            ),
            "above_threshold": (
                v["op_threshold"] is not None and v["prob"] >= v["op_threshold"]
            ),
            "threshold_margin": (
                round(v["threshold_margin"], 4)
                if v["threshold_margin"] is not None
                else None
            ),
            "threshold_band": v["threshold_band"],
            "ambiguity": v["ambiguity"],
            "in_pneumonia_group": name in xray_model.PNEUMONIA_GROUP,
        }
        for name, v in ranked
    ]


def _get_inference_artifacts(
    data: bytes,
    filename: str,
    estimate_stability: bool = False,
    progress_cb=None,
) -> dict:
    """Pré-processa e infere, reutilizando cache intermediário por arquivo."""

    def report(**kwargs):
        if progress_cb is not None:
            progress_cb(**kwargs)

    inf_key = analysis_cache.fingerprint(
        data, filename, extras=f"inference|{int(estimate_stability)}"
    )
    with _inference_lock:
        cached = _inference_cache.get(inf_key)
        if cached is not None:
            report(progress=0.55, stage="inference-cache")
            return cached

    report(progress=0.15, stage="preprocessing")
    preprocessing_started = time.perf_counter()
    try:
        raw, image_metadata = imaging.load_image_with_metadata(data, filename)
        input_quality = imaging.assess_quality(raw)
        radiograph_qc = assess_radiograph_quality(raw)
        tensor, vis_u8 = imaging.preprocess(raw)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Falha ao ler a imagem: {exc}") from exc
    preprocessing_ms = (time.perf_counter() - preprocessing_started) * 1000

    report(progress=0.45, stage="inference")
    inference_started = time.perf_counter()
    probs = xray_model.predict(tensor)
    inference_ms = (time.perf_counter() - inference_started) * 1000

    stability = None
    stability_ms = 0.0
    if estimate_stability:
        report(progress=0.85, stage="stability")
        stability_started = time.perf_counter()
        stability = estimate_prediction_stability(tensor, samples=3)
        stability_ms = (time.perf_counter() - stability_started) * 1000

    artifacts = {
        "tensor": tensor,
        "vis_u8": vis_u8,
        "probs": probs,
        "input_quality": input_quality,
        "radiograph_quality": radiograph_qc,
        "image_metadata": image_metadata,
        "prediction_stability": stability,
        "timings": {
            "preprocessing_ms": round(preprocessing_ms, 2),
            "inference_ms": round(inference_ms, 2),
            "stability_ms": round(stability_ms, 2),
        },
    }
    with _inference_lock:
        _inference_cache[inf_key] = artifacts
        while len(_inference_cache) > 16:
            _inference_cache.pop(next(iter(_inference_cache)))
    return artifacts


def _analyze_for_comparison(data: bytes, filename: str) -> dict:
    cache_key = analysis_cache.fingerprint(data, filename, extras="compare")
    cached = analysis_cache.get(cache_key)
    if cached is not None:
        return dict(cached)

    artifacts = _get_inference_artifacts(data, filename, estimate_stability=False)
    payload = {
        "probabilities": artifacts["probs"],
        "image": overlay.gray_to_b64(artifacts["vis_u8"]),
        "quality": artifacts["input_quality"],
        "radiograph_quality": artifacts["radiograph_quality"],
        "metadata": artifacts["image_metadata"],
        "decision_context": xray_model.decision_context(artifacts["probs"]),
    }
    analysis_cache.set(cache_key, payload)
    return dict(payload)


@app.get("/api/info")
def api_info():
    """Metadados estáveis da API para clientes e badges da UI."""
    return {
        "name": "thorax-triage",
        "api_version": app.version,
        "capabilities": [
            "analyze",
            "analyze-async",
            "analyze-gradcam",
            "compare",
            "radiograph-qc",
            "prediction-stability",
            "cache",
            "job-cancel",
        ],
        "disclaimer": (
            "Protótipo de pesquisa e ensino. Não substitui avaliação médica."
        ),
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
        "cache": analysis_cache.stats(),
        "capabilities": api_info()["capabilities"],
        "rate_limit": {
            "max_requests": rate_limiter.max_requests,
            "window_seconds": rate_limiter.window_seconds,
        },
    }


@app.get("/api/nih-manifest")
def nih_manifest():
    """Devolve o manifesto NIH apenas com imagens presentes no disco."""
    manifest_path = NIH_DEMO_DIR / "manifest.json"
    if not manifest_path.exists():
        return {
            "available": False,
            "count": 0,
            "images": [],
            "message": (
                "Pack NIH não encontrado. Execute: npm run download:nih-demo"
            ),
            "download_command": "npm run download:nih-demo",
        }
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao ler o manifesto NIH: {exc}",
        ) from exc

    images = []
    for entry in payload.get("images", []):
        relative = entry.get("path") or f"assets/nih-demo/{entry.get('image_index', '')}"
        absolute = Path(PROJECT_DIR) / relative
        if absolute.exists():
            images.append({**entry, "path": relative.replace("\\", "/")})
    return {
        "available": bool(images),
        "count": len(images),
        "images": images,
        "dataset": payload.get("dataset", "NIH ChestX-ray14"),
        "provider": payload.get("provider", "NIH Clinical Center"),
        "source": payload.get("source"),
        "disclaimer": payload.get("disclaimer"),
        "message": (
            None
            if images
            else "Nenhuma imagem NIH encontrada. Execute: npm run download:nih-demo"
        ),
        "download_command": "npm run download:nih-demo",
    }


def _build_analyze_payload(
    data: bytes,
    filename: str,
    target_pathology: str | None = None,
    estimate_stability: bool = False,
    progress_cb=None,
) -> dict:
    """Executa o pipeline de análise e devolve o payload JSON."""

    def report(**kwargs):
        if progress_cb is not None:
            progress_cb(**kwargs)

    request_started = time.perf_counter()
    cache_key = analysis_cache.fingerprint(
        data,
        filename,
        extras=f"{target_pathology or ''}|{int(estimate_stability)}",
    )
    cached = analysis_cache.get(cache_key)
    if cached is not None:
        payload = dict(cached)
        payload["cache"] = {"hit": True, **analysis_cache.stats()}
        payload["timings"] = {
            **payload.get("timings", {}),
            "total_ms": round((time.perf_counter() - request_started) * 1000, 2),
        }
        report(progress=1.0, stage="cache")
        return payload

    artifacts = _get_inference_artifacts(
        data,
        filename,
        estimate_stability=estimate_stability,
        progress_cb=progress_cb,
    )
    probs = artifacts["probs"]
    if target_pathology and target_pathology not in probs:
        raise ValueError(f"Patologia-alvo desconhecida: {target_pathology}.")
    target = target_pathology or xray_model.top_target(probs)

    report(progress=0.7, stage="gradcam")
    gradcam_started = time.perf_counter()
    cam = xray_model.gradcam(artifacts["tensor"], target)
    gradcam_ms = (time.perf_counter() - gradcam_started) * 1000

    payload = {
        "target_pathology": target,
        "pneumonia_group": xray_model.PNEUMONIA_GROUP,
        "predictions": _predictions_payload(probs),
        "image_original": overlay.gray_to_b64(artifacts["vis_u8"]),
        "image_overlay": overlay.make_overlay(artifacts["vis_u8"], cam),
        "input_quality": artifacts["input_quality"],
        "radiograph_quality": artifacts["radiograph_quality"],
        "image_metadata": artifacts["image_metadata"],
        "decision_context": xray_model.decision_context(probs),
        "prediction_stability": artifacts["prediction_stability"],
        "explainability": {
            "target_pathology": target,
            "cam_stats": xray_model.cam_stats(cam),
            "note": (
                "O mapa representa atenção do modelo e não delimita uma lesão."
            ),
        },
        "timings": {
            **artifacts["timings"],
            "gradcam_ms": round(gradcam_ms, 2),
            "total_ms": round((time.perf_counter() - request_started) * 1000, 2),
        },
        "disclaimer": (
            "Prototipo de pesquisa e ensino. Nao substitui avaliacao medica "
            "nem laudo radiologico. Nao usar em decisao clinica real."
        ),
    }
    analysis_cache.set(cache_key, payload)
    payload = dict(payload)
    payload["cache"] = {"hit": False, **analysis_cache.stats()}
    report(progress=0.98, stage="finalizing")
    return payload


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    target_pathology: str | None = Form(default=None),
    estimate_stability: bool = Form(default=False),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")
    _validate_upload(file, data)
    try:
        return _build_analyze_payload(
            data,
            file.filename or "",
            target_pathology=target_pathology,
            estimate_stability=estimate_stability,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/analyze/gradcam")
async def analyze_gradcam(
    file: UploadFile = File(...),
    target_pathology: str = Form(...),
    estimate_stability: bool = Form(default=False),
):
    """Recalcula apenas o Grad-CAM reutilizando a inferência em cache."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")
    _validate_upload(file, data)
    try:
        request_started = time.perf_counter()
        artifacts = _get_inference_artifacts(
            data,
            file.filename or "",
            estimate_stability=estimate_stability,
        )
        probs = artifacts["probs"]
        if target_pathology not in probs:
            raise ValueError(f"Patologia-alvo desconhecida: {target_pathology}.")
        gradcam_started = time.perf_counter()
        cam = xray_model.gradcam(artifacts["tensor"], target_pathology)
        gradcam_ms = (time.perf_counter() - gradcam_started) * 1000
        return {
            "target_pathology": target_pathology,
            "pneumonia_group": xray_model.PNEUMONIA_GROUP,
            "predictions": _predictions_payload(probs),
            "image_original": overlay.gray_to_b64(artifacts["vis_u8"]),
            "image_overlay": overlay.make_overlay(artifacts["vis_u8"], cam),
            "input_quality": artifacts["input_quality"],
            "radiograph_quality": artifacts["radiograph_quality"],
            "image_metadata": artifacts["image_metadata"],
            "decision_context": xray_model.decision_context(probs),
            "prediction_stability": artifacts["prediction_stability"],
            "explainability": {
                "target_pathology": target_pathology,
                "cam_stats": xray_model.cam_stats(cam),
                "note": (
                    "O mapa representa atenção do modelo e não delimita uma lesão."
                ),
            },
            "timings": {
                **artifacts["timings"],
                "gradcam_ms": round(gradcam_ms, 2),
                "total_ms": round((time.perf_counter() - request_started) * 1000, 2),
            },
            "cache": {"hit": True, "mode": "inference-reuse", **analysis_cache.stats()},
            "disclaimer": (
                "Prototipo de pesquisa e ensino. Nao substitui avaliacao medica "
                "nem laudo radiologico. Nao usar em decisao clinica real."
            ),
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/analyze/async")
async def analyze_async(
    file: UploadFile = File(...),
    target_pathology: str | None = Form(default=None),
    estimate_stability: bool = Form(default=False),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")
    _validate_upload(file, data)
    job = job_store.create()
    filename = file.filename or ""

    def worker(report):
        return _build_analyze_payload(
            data,
            filename,
            target_pathology=target_pathology,
            estimate_stability=estimate_stability,
            progress_cb=report,
        )

    threading.Thread(
        target=run_job,
        args=(job.id, worker),
        daemon=True,
    ).start()
    return {"job_id": job.id, "status": job.status}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    return job_store.to_dict(job)


@app.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    job = job_store.cancel(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    return job_store.to_dict(job)


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
        "radiograph_quality_a": analysis_a.get("radiograph_quality"),
        "radiograph_quality_b": analysis_b.get("radiograph_quality"),
        "metadata_a": analysis_a["metadata"],
        "metadata_b": analysis_b["metadata"],
        "decision_context_a": analysis_a.get("decision_context"),
        "decision_context_b": analysis_b.get("decision_context"),
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


@app.post("/admin/cache/clear")
def clear_cache(x_admin_token: str | None = Header(default=None)):
    if not ADMIN_TOKEN:
        raise HTTPException(status_code=404, detail="Endpoint não disponível.")
    if not x_admin_token or x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Token administrativo inválido.")
    removed = analysis_cache.clear()
    with _inference_lock:
        _inference_cache.clear()
    return {"cleared": removed, "cache": analysis_cache.stats()}


@app.get("/")
def index():
    return FileResponse(os.path.join(PROJECT_DIR, "index.html"))


app.mount("/assets", StaticFiles(directory=os.path.join(PROJECT_DIR, "assets")), name="assets")


@app.get("/{filename:path}")
def frontend_file(filename: str):
    """Serve os arquivos estáticos do protótipo sem expor arquivos Python."""
    allowed = {
        "app.js",
        "data.js",
        "glossary.js",
        "history.js",
        "styles.css",
        "viewer.js",
    }
    if filename not in allowed:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    return FileResponse(os.path.join(PROJECT_DIR, filename))
