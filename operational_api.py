"""Extensões operacionais instaladas sobre a aplicação FastAPI existente."""
from __future__ import annotations

import time

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

import xray_model
from analysis_cache import cache as analysis_cache
from config import settings
from healthchecks import liveness_payload, readiness_payload
from jobs import store as job_store
from model_metadata import build_model_card
from rate_limit import limiter as rate_limiter
from request_context import normalize_request_id
from runtime_metrics import metrics


def install_operational_features(app):
    """Instala rotas e telemetria sem alterar os endpoints de análise legados."""
    if getattr(app.state, "operational_features_installed", False):
        return app

    @app.middleware("http")
    async def normalized_request_context(request: Request, call_next):
        request_id = normalize_request_id(
            request.headers.get("X-Request-ID"),
            max_length=settings.request_id_max_length,
        )
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        route = request.scope.get("route")
        metric_path = getattr(route, "path", request.url.path)
        if settings.metrics_enabled:
            metrics.record_request(metric_path, response.status_code, duration_ms)
            if response.status_code == 429:
                metrics.record_rate_limited()
            if response.status_code == 413:
                metrics.record_upload_rejection()
        response.headers["X-Request-ID"] = request_id
        return response

    def health_live():
        return liveness_payload(app.version)

    def health_ready():
        payload, status_code = readiness_payload(app.version, xray_model.get_model)
        if status_code == 200:
            return payload
        return JSONResponse(status_code=status_code, content=payload)

    def metrics_payload():
        if not settings.metrics_enabled:
            raise HTTPException(status_code=404, detail="Métricas desabilitadas.")
        return {
            "runtime": metrics.snapshot(),
            "cache": analysis_cache.stats(),
            "jobs": job_store.stats(),
            "rate_limit": rate_limiter.stats(),
        }

    def model_card():
        return build_model_card(xray_model.get_model(), weights=xray_model.WEIGHTS)

    def runtime_config():
        return settings.public_dict()

    app.add_api_route("/health/live", health_live, methods=["GET"], tags=["operations"])
    app.add_api_route("/health/ready", health_ready, methods=["GET"], tags=["operations"])
    app.add_api_route("/metrics", metrics_payload, methods=["GET"], tags=["operations"])
    app.add_api_route("/api/model", model_card, methods=["GET"], tags=["metadata"])
    app.add_api_route("/api/config", runtime_config, methods=["GET"], tags=["metadata"])
    app.state.operational_features_installed = True
    return app
