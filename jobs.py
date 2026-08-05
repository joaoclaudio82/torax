"""
Fila simples em memória para análises assíncronas educacionais.
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Job:
    id: str
    status: str = "queued"
    progress: float = 0.0
    stage: str = "queued"
    result: dict | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class JobStore:
    def __init__(self, max_jobs: int = 64):
        self.max_jobs = max_jobs
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self) -> Job:
        job = Job(id=str(uuid.uuid4()))
        with self._lock:
            self._jobs[job.id] = job
            while len(self._jobs) > self.max_jobs:
                oldest = min(self._jobs.values(), key=lambda item: item.created_at)
                del self._jobs[oldest.id]
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

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
            if status is not None:
                job.status = status
            if progress is not None:
                job.progress = progress
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
        }


store = JobStore()


def run_job(job_id: str, worker: Callable[[Callable[..., None]], dict]) -> None:
    def report(**kwargs) -> None:
        store.update(job_id, **kwargs)

    store.update(job_id, status="running", progress=0.05, stage="starting")
    try:
        result = worker(report)
        store.update(
            job_id,
            status="completed",
            progress=1.0,
            stage="done",
            result=result,
        )
    except Exception as exc:  # noqa: BLE001
        store.update(
            job_id,
            status="failed",
            progress=1.0,
            stage="error",
            error=str(exc),
        )
