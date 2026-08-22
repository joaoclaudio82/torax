import asyncio

import pytest

from upload_utils import UploadTooLarge, read_upload_limited


class FakeUpload:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.offset = 0

    async def read(self, size: int = -1) -> bytes:
        if self.offset >= len(self.payload):
            return b""
        if size < 0:
            size = len(self.payload) - self.offset
        chunk = self.payload[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk


def test_read_upload_limited_accepts_payload_within_limit():
    upload = FakeUpload(b"abcdef")
    result = asyncio.run(read_upload_limited(upload, 6, chunk_size=2))
    assert result == b"abcdef"


def test_read_upload_limited_rejects_oversized_payload_early():
    upload = FakeUpload(b"abcdefgh")
    with pytest.raises(UploadTooLarge):
        asyncio.run(read_upload_limited(upload, 5, chunk_size=2))
    assert upload.offset <= 6


def test_read_upload_limited_validates_limits():
    upload = FakeUpload(b"x")
    with pytest.raises(ValueError):
        asyncio.run(read_upload_limited(upload, 0))
