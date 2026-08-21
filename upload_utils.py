"""Leitura limitada de uploads para evitar alocação desnecessária de memória."""
from __future__ import annotations


class UploadTooLarge(ValueError):
    """Sinaliza que o upload excedeu o limite configurado."""


def _validate_limits(max_bytes: int, chunk_size: int) -> None:
    if max_bytes < 1:
        raise ValueError("max_bytes deve ser positivo")
    if chunk_size < 1:
        raise ValueError("chunk_size deve ser positivo")


async def read_upload_limited(
    upload,
    max_bytes: int,
    *,
    chunk_size: int = 1024 * 1024,
) -> bytes:
    """Lê UploadFile em blocos e interrompe assim que o limite é excedido."""
    _validate_limits(max_bytes, chunk_size)
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise UploadTooLarge(
                f"Upload excede o limite configurado de {max_bytes} bytes."
            )
        chunks.append(chunk)
    return b"".join(chunks)
