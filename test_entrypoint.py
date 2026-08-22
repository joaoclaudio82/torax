import entrypoint
from config import settings


def test_entrypoint_synchronizes_legacy_runtime_settings():
    assert entrypoint.legacy_main.MAX_UPLOAD_BYTES == settings.max_upload_bytes
    assert entrypoint.legacy_main.ADMIN_TOKEN == settings.admin_token
    assert entrypoint.base_app.version == "2.3.0"


def test_entrypoint_installs_operational_features():
    paths = {getattr(route, "path", None) for route in entrypoint.base_app.router.routes}
    assert "/health/live" in paths
    assert "/health/ready" in paths
    assert "/metrics" in paths
    assert "/api/model" in paths
