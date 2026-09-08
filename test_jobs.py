import time

from jobs import JobStore, run_job


def test_job_store_cancels_running_job():
    store = JobStore(max_jobs=8, ttl_seconds=60)
    job = store.create()
    cancelled = store.cancel(job.id)
    assert cancelled is not None
    assert cancelled.status == "cancelled"
    assert store.is_cancelled(job.id) is True


def test_job_store_purges_expired_terminal_entries():
    store = JobStore(max_jobs=8, ttl_seconds=1)
    job = store.create()
    store.update(job.id, status="completed")
    job.updated_at = time.time() - 5
    assert store.get(job.id) is None
    assert store.stats()["purged_expired"] == 1


def test_running_job_is_not_purged_by_ttl():
    store = JobStore(max_jobs=8, ttl_seconds=1)
    job = store.create()
    store.update(job.id, status="running")
    job.updated_at = time.time() - 5
    assert store.get(job.id) is not None


def test_job_store_clamps_progress():
    store = JobStore(max_jobs=8, ttl_seconds=60)
    job = store.create()
    store.update(job.id, progress=2.5)
    assert store.get(job.id).progress == 1.0
    store.update(job.id, progress=-1)
    assert store.get(job.id).progress == 0.0


def test_job_store_exposes_status_counts():
    store = JobStore(max_jobs=8, ttl_seconds=60)
    queued = store.create()
    running = store.create()
    store.update(running.id, status="running")
    stats = store.stats()
    assert stats["jobs"] == 2
    assert stats["status_counts"]["queued"] == 1
    assert stats["status_counts"]["running"] == 1
    assert queued.id != running.id


def test_job_store_rejects_when_active_capacity_is_full():
    store = JobStore(max_jobs=2, ttl_seconds=60)
    first = store.create()
    second = store.create()
    store.update(first.id, status="running")
    store.update(second.id, status="running")

    rejected = store.create()

    assert rejected.status == "rejected"
    assert rejected.stage == "capacity"
    assert store.rejected_capacity == 1
    assert store.get(first.id) is not None
    assert store.get(second.id) is not None


def test_run_job_respects_cancellation():
    from jobs import store as global_store

    job = global_store.create()
    global_store.cancel(job.id)

    def worker(report):
        report(progress=0.2, stage="preprocessing")
        return {"ok": True}

    run_job(job.id, worker)
    refreshed = global_store.get(job.id)
    assert refreshed.status == "cancelled"
