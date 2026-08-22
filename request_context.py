"""Normalização de identificadores de requisição usados em logs e headers."""
from __future__ import annotations

import re
import uuid


_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]+$")


def normalize_request_id(value: str | None, *, max_length: int = 128) -> str:
    candidate = (value or "").strip()
    if (
        not candidate
        or len(candidate) > max_length
        or not _REQUEST_ID_RE.fullmatch(candidate)
    ):
        return str(uuid.uuid4())
    return candidate
