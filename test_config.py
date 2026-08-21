from config import load_settings


def test_defaults_are_safe():
    cfg = load_settings({})
    assert cfg.max_upload_mb == 15
    assert cfg.rate_limit_max == 30
    assert cfg.trust_proxy is False
    assert cfg.metrics_enabled is True
    assert cfg.admin_token == ""


def test_environment_overrides_are_parsed():
    cfg = load_settings(
        {
            "THORAX_ALLOWED_ORIGINS": "https://a.example, https://b.example",
            "THORAX_MAX_UPLOAD_MB": "20",
            "THORAX_RATE_LIMIT_MAX": "50",
            "THORAX_TRUST_PROXY": "true",
            "THORAX_METRICS_ENABLED": "0",
            "THORAX_ADMIN_TOKEN": " secret ",
        }
    )
    assert cfg.allowed_origins == ("https://a.example", "https://b.example")
    assert cfg.max_upload_mb == 20
    assert cfg.rate_limit_max == 50
    assert cfg.trust_proxy is True
    assert cfg.metrics_enabled is False
    assert cfg.admin_token == "secret"


def test_invalid_or_out_of_range_values_fall_back():
    cfg = load_settings(
        {
            "THORAX_MAX_UPLOAD_MB": "9999",
            "THORAX_RATE_LIMIT_MAX": "invalid",
            "THORAX_JOB_TTL_SECONDS": "1",
        }
    )
    assert cfg.max_upload_mb == 15
    assert cfg.rate_limit_max == 30
    assert cfg.job_ttl_seconds == 1800


def test_public_dict_never_exposes_admin_token():
    cfg = load_settings({"THORAX_ADMIN_TOKEN": "top-secret"})
    payload = cfg.public_dict()
    assert "admin_token" not in payload
    assert "top-secret" not in repr(payload)
