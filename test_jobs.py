import time

from jobs import JobCancelled, JobStore, run_job


def test_job_store_cancels_running_job():
    store = JobStore(max_jobs=8, ttl_seconds=60)
    job = store.create()
    cancelled = store.cancel(job.id)
    assert cancelled is not None
    assert cancelled.status == "cancelled"
    assert store.is_cancelled(job.id) is True


def test_job_store_purges_expired_entries():
    store = JobStore(max_jobs=8, ttl_seconds=1)
    job = store.create()
    job.updated_at = time.time() - 5
    assert store.get(job.id) is None


def test_run_job_respects_cancellation(monkeypatch):
    from jobs import store as global_store

    job = global_store.create()
    global_store.cancel(job.id)

    def worker(report):
        report(progress=0.2, stage="preprocessing")
        return {"ok": True}

    run_job(job.id, worker)
    refreshed = global_store.get(job.id)
    assert refreshed.status == "cancelled"
