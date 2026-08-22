import uuid

from request_context import normalize_request_id


def test_valid_request_id_is_preserved():
    assert normalize_request_id("abc-123_trace") == "abc-123_trace"


def test_invalid_request_id_is_replaced():
    generated = normalize_request_id("bad\nheader")
    uuid.UUID(generated)
    assert generated != "bad\nheader"


def test_oversized_request_id_is_replaced():
    generated = normalize_request_id("x" * 129, max_length=128)
    uuid.UUID(generated)
