"""Entrypoint ASGI composto com recursos operacionais e limites defensivos."""
from __future__ import annotations

from body_limit import RequestBodyLimitMiddleware
from config import settings
import main as legacy_main
from operational_api import install_operational_features
from runtime_metrics import metrics


# Sincroniza constantes legadas com a configuração central antes de atender tráfego.
legacy_main.MAX_UPLOAD_BYTES = settings.max_upload_bytes
legacy_main.ADMIN_TOKEN = settings.admin_token

base_app = legacy_main.app
base_app.version = "2.3.0"
install_operational_features(base_app)

app = RequestBodyLimitMiddleware(
    base_app,
    max_upload_bytes=settings.max_upload_bytes,
    on_reject=metrics.record_upload_rejection,
    request_id_max_length=settings.request_id_max_length,
)
