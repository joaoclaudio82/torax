"""Limite defensivo do corpo HTTP antes do parser multipart da aplicação."""
from __future__ import annotations

import json
from typing import Callable

from request_context import normalize_request_id


_MULTIPART_OVERHEAD_BYTES = 2 * 1024 * 1024


def request_body_limit(path: str, max_upload_bytes: int) -> int | None:
    """Define o teto do corpo HTTP considerando arquivos e overhead multipart."""
    if path == "/compare":
        return (2 * max_upload_bytes) + _MULTIPART_OVERHEAD_BYTES
    if path.startswith("/analyze"):
        return max_upload_bytes + _MULTIPART_OVERHEAD_BYTES
    return None


class RequestBodyLimitMiddleware:
    """ASGI wrapper que rejeita corpos excessivos, inclusive transferências chunked."""

    def __init__(
        self,
        app,
        *,
        max_upload_bytes: int,
        on_reject: Callable[[], None] | None = None,
        request_id_max_length: int = 128,
    ) -> None:
        self.app = app
        self.max_upload_bytes = max_upload_bytes
        self.on_reject = on_reject
        self.request_id_max_length = request_id_max_length

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        limit = request_body_limit(path, self.max_upload_bytes)
        if limit is None:
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                if int(content_length) > limit:
                    await self._reject(scope, send, limit)
                    return
            except ValueError:
                pass

        messages: list[dict] = []
        total = 0
        while True:
            message = await receive()
            messages.append(message)
            if message.get("type") == "http.request":
                total += len(message.get("body", b""))
                if total > limit:
                    await self._reject(scope, send, limit)
                    return
                if not message.get("more_body", False):
                    break
            elif message.get("type") == "http.disconnect":
                break

        index = 0

        async def replay_receive():
            nonlocal index
            if index < len(messages):
                message = messages[index]
                index += 1
                return message
            return {"type": "http.request", "body": b"", "more_body": False}

        await self.app(scope, replay_receive, send)

    async def _reject(self, scope, send, limit: int) -> None:
        if self.on_reject is not None:
            self.on_reject()
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        raw_request_id = headers.get(b"x-request-id", b"").decode("utf-8", errors="ignore")
        request_id = normalize_request_id(
            raw_request_id,
            max_length=self.request_id_max_length,
        )
        payload = json.dumps(
            {
                "detail": "Corpo da requisição excede o limite permitido.",
                "max_request_bytes": limit,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json; charset=utf-8"),
                    (b"content-length", str(len(payload)).encode("ascii")),
                    (b"x-request-id", request_id.encode("ascii")),
                    (b"x-content-type-options", b"nosniff"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": payload})
