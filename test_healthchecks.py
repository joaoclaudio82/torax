from healthchecks import liveness_payload, readiness_payload


class FakeModel:
    pathologies = ["A", "B", ""]


def test_liveness_does_not_require_model():
    payload = liveness_payload("3.0")
    assert payload["status"] == "ok"
    assert payload["api_version"] == "3.0"
    assert payload["uptime_seconds"] >= 0


def test_readiness_reports_loaded_model():
    payload, status = readiness_payload("3.0", lambda: FakeModel())
    assert status == 200
    assert payload["status"] == "ready"
    assert payload["pathologies"] == 2


def test_readiness_returns_503_without_leaking_exception_message():
    def fail():
        raise RuntimeError("secret path /tmp/model.bin")

    payload, status = readiness_payload("3.0", fail)
    assert status == 503
    assert payload["error_type"] == "RuntimeError"
    assert "secret path" not in repr(payload)
