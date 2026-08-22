"""Configuração centralizada e tolerante a ambiente para o protótipo."""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Mapping


def _env_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _bounded_int(
    environ: Mapping[str, str],
    name: str,
    default: int,
    *,
    minimum: int,
    maximum: int,
) -> int:
    raw = environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if minimum <= value <= maximum else default


def _origins(environ: Mapping[str, str]) -> tuple[str, ...]:
    raw = environ.get(
        "THORAX_ALLOWED_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000",
    )
    values = tuple(item.strip() for item in raw.split(",") if item.strip())
    return values or ("http://localhost:8000", "http://127.0.0.1:8000")


@dataclass(frozen=True)
class Settings:
    allowed_origins: tuple[str, ...]
    admin_token: str
    trust_proxy: bool
    max_upload_bytes: int
    rate_limit_max: int
    rate_limit_window_seconds: int
    job_max: int
    job_ttl_seconds: int
    cache_max_entries: int
    cache_ttl_seconds: int
    metrics_enabled: bool
    request_id_max_length: int

    @property
    def max_upload_mb(self) -> int:
        return max(1, self.max_upload_bytes // (1024 * 1024))

    def public_dict(self) -> dict:
        """Configuração segura para observabilidade; nunca expõe o token admin."""
        return {
            "allowed_origins": list(self.allowed_origins),
            "trust_proxy": self.trust_proxy,
            "max_upload_mb": self.max_upload_mb,
            "rate_limit_max": self.rate_limit_max,
            "rate_limit_window_seconds": self.rate_limit_window_seconds,
            "job_max": self.job_max,
            "job_ttl_seconds": self.job_ttl_seconds,
            "cache_max_entries": self.cache_max_entries,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "metrics_enabled": self.metrics_enabled,
        }


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    env = os.environ if environ is None else environ
    max_upload_mb = _bounded_int(
        env,
        "THORAX_MAX_UPLOAD_MB",
        15,
        minimum=1,
        maximum=100,
    )
    return Settings(
        allowed_origins=_origins(env),
        admin_token=env.get("THORAX_ADMIN_TOKEN", "").strip(),
        trust_proxy=_env_bool(env.get("THORAX_TRUST_PROXY"), False),
        max_upload_bytes=max_upload_mb * 1024 * 1024,
        rate_limit_max=_bounded_int(
            env, "THORAX_RATE_LIMIT_MAX", 30, minimum=1, maximum=10000
        ),
        rate_limit_window_seconds=_bounded_int(
            env, "THORAX_RATE_LIMIT_WINDOW", 60, minimum=1, maximum=86400
        ),
        job_max=_bounded_int(env, "THORAX_JOB_MAX", 64, minimum=1, maximum=10000),
        job_ttl_seconds=_bounded_int(
            env, "THORAX_JOB_TTL_SECONDS", 1800, minimum=30, maximum=604800
        ),
        cache_max_entries=_bounded_int(
            env, "THORAX_CACHE_MAX_ENTRIES", 32, minimum=1, maximum=10000
        ),
        cache_ttl_seconds=_bounded_int(
            env, "THORAX_CACHE_TTL_SECONDS", 1800, minimum=30, maximum=604800
        ),
        metrics_enabled=_env_bool(env.get("THORAX_METRICS_ENABLED"), True),
        request_id_max_length=_bounded_int(
            env, "THORAX_REQUEST_ID_MAX_LENGTH", 128, minimum=16, maximum=512
        ),
    )


settings = load_settings()
