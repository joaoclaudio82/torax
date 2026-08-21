"""Contratos de liveness e readiness separados para operação do serviço."""
from __future__ import annotations

import time
from typing import Callable


_BOOT_TIME = time.time()


def liveness_payload(version: str) -> dict:
    return {
        "status": "ok",
        "api_version": version,
        "uptime_seconds": round(max(0.0, time.time() - _BOOT_TIME), 3),
    }


def readiness_payload(version: str, model_loader: Callable[[], object]) -> tuple[dict, int]:
    try:
        model = model_loader()
        pathologies = [item for item in getattr(model, "pathologies", []) if item]
        return (
            {
                "status": "ready",
                "api_version": version,
                "model_loaded": True,
                "pathologies": len(pathologies),
            },
            200,
        )
    except Exception as exc:  # noqa: BLE001
        return (
            {
                "status": "not_ready",
                "api_version": version,
                "model_loaded": False,
                "error_type": type(exc).__name__,
            },
            503,
        )
