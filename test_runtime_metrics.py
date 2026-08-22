from runtime_metrics import RuntimeMetrics


def test_runtime_metrics_aggregate_requests():
    metrics = RuntimeMetrics()
    metrics.record_request("/health", 200, 10.0)
    metrics.record_request("/health", 200, 30.0)
    metrics.record_request("/analyze", 422, 20.0)
    snapshot = metrics.snapshot()
    assert snapshot["requests_total"] == 3
    assert snapshot["request_duration_ms_avg"] == 20.0
    assert snapshot["status_codes"] == {"200": 2, "422": 1}
    assert snapshot["paths"]["/health"] == 2


def test_runtime_metrics_track_protection_events():
    metrics = RuntimeMetrics()
    metrics.record_rate_limited()
    metrics.record_upload_rejection()
    snapshot = metrics.snapshot()
    assert snapshot["rate_limited_total"] == 1
    assert snapshot["upload_rejections_total"] == 1


def test_runtime_metrics_reset_clears_counters():
    metrics = RuntimeMetrics()
    metrics.record_request("/x", 200, 1)
    metrics.reset()
    assert metrics.snapshot()["requests_total"] == 0
