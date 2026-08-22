"""
Fila simples em memória para análises assíncronas educacionais.
"""
from __future__ import annotations

from collections import Counter
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from config import settings


@dataclass
class Job:
    id: str
    status: str = "queued"
    progress: float = 0.0
    stage: str = "queued"
    result: dict | None = None
    error: str | None = None
    cancel_requested: bool = False
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class JobStore:
    def __init__(
        self,
        max_jobs: int | None = None,
        ttl_seconds: int | None = None,
    ):
        self.max_jobs = max_jobs if max_jobs is not None else settings.job_max
        self.ttl_seconds = (
            ttl_seconds if ttl_seconds is not None else settings.job_ttl_seconds
        )
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self.purged_expired = 0
        self.purged_overflow = 0

    def _purge_locked(self, now: float | None = None) -> None:
        now = time.time() if now is None else now
        expired = [
            job_id
            for job_id, job in self._jobs.items()
            if now - job.updated_at > self.ttl_seconds
        ]
        for job_id in expired:
            del self._jobs[job_id]
            self.purged_expired += 1
        while len(self._jobs) > self.max_jobs:
            oldest = min(self._jobs.values(), key=lambda item: item.created_at)
            del self._jobs[oldest.id]
            self.purged_overflow += 1

    def create(self) -> Job:
        job = Job(id=str(uuid.uuid4()))
        with self._lock:
            self._purge_locked()
            self._jobs[job.id] = job
            self._purge_locked()
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            self._purge_locked()
            return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            job.cancel_requested = True
            if job.status in {"queued", "running"}:
                job.status = "cancelled"
                job.stage = "cancelled"
                job.progress = 1.0
                job.error = "Cancelado pelo cliente."
            job.updated_at = time.time()
            return job

    def is_cancelled(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            return bool(job and (job.cancel_requested or job.status == "cancelled"))

    def update(
        self,
        job_id: str,
        *,
        status: str | None = None,
        progress: float | None = None,
        stage: str | None = None,
        result: dict | None = None,
        error: str | None = None,
    ) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            if job.cancel_requested and status not in {"cancelled", "failed"}:
                job.status = "cancelled"
                job.stage = "cancelled"
                job.progress = 1.0
                job.updated_at = time.time()
                return
            if status is not None:
                job.status = status
            if progress is not None:
                job.progress = max(0.0, min(1.0, float(progress)))
            if stage is not None:
                job.stage = stage
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error
            job.updated_at = time.time()

    def to_dict(self, job: Job) -> dict[str, Any]:
        return {
            "id": job.id,
            "status": job.status,
            "progress": job.progress,
            "stage": job.stage,
            "error": job.error,
            "result": job.result,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "cancel_requested": job.cancel_requested,
        }

    def stats(self) -> dict:
        with self._lock:
            self._purge_locked()
            counts = Counter(job.status for job in self._jobs.values())
            return {
                "jobs": len(self._jobs),
                "status_counts": dict(counts),
                "max_jobs": self.max_jobs,
                "ttl_seconds": self.ttl_seconds,
                "purged_expired": self.purged_expired,
                "purged_overflow": self.purged_overflow,
            }


store = JobStore()


class JobCancelled(Exception):
    """Sinaliza cancelamento cooperativo do worker."""


def run_job(job_id: str, worker: Callable[[Callable[..., None]], dict]) -> None:
    def report(**kwargs) -> None:
        if store.is_cancelled(job_id):
            raise JobCancelled()
        store.update(job_id, **kwargs)

    if store.is_cancelled(job_id):
        return

    store.update(job_id, status="running", progress=0.05, stage="starting")
    try:
        result = worker(report)
        if store.is_cancelled(job_id):
            store.update(
                job_id,
                status="cancelled",
                progress=1.0,
                stage="cancelled",
                error="Cancelado pelo cliente.",
            )
            return
        store.update(
            job_id,
            status="completed",
            progress=1.0,
            stage="done",
            result=result,
        )
    except JobCancelled:
        store.update(
            job_id,
            status="cancelled",
            progress=1.0,
            stage="cancelled",
            error="Cancelado pelo cliente.",
        )
    except Exception as exc:  # noqa: BLE001
        store.update(
            job_id,
            status="failed",
            progress=1.0,
            stage="error",
            error=str(exc),
        )
