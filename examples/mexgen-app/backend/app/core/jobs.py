"""In-memory async job manager for explanation tasks.

Each job runs the full MExGen pipeline in a background thread so the
API stays responsive. Progress is broadcast via an asyncio Event system
that the WebSocket handler subscribes to.
"""

from __future__ import annotations

import asyncio
import logging
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from app.core.explainer import explain_coarse, explain_fine, generate_output
from app.core.models import registry
from app.schemas.types import (
    AttributionMethod,
    ExplainResponse,
    JobStatus,
    TaskType,
    UnitAttribution,
)

logger = logging.getLogger(__name__)

# Single worker: explanation is GPU-bound, parallelism doesn't help
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mexgen")


@dataclass
class Job:
    id: str
    document: str
    task: TaskType
    question: str | None
    method: AttributionMethod
    scalarizer: str
    status: JobStatus = JobStatus.pending
    progress: float = 0.0
    generated_output: str | None = None
    attributions: list[UnitAttribution] = field(default_factory=list)
    error: str | None = None
    # asyncio Event pulsed on every state change so WS listeners wake up
    _event: asyncio.Event = field(default_factory=asyncio.Event)

    def to_response(self) -> ExplainResponse:
        return ExplainResponse(
            job_id=self.id,
            status=self.status,
            task=self.task,
            document=self.document,
            question=self.question,
            generated_output=self.generated_output,
            attributions=self.attributions,
            progress=self.progress,
            error=self.error,
        )

    def notify(self) -> None:
        self._event.set()
        self._event.clear()

    async def wait_for_change(self, timeout: float = 30.0) -> None:
        try:
            await asyncio.wait_for(self._event.wait(), timeout)
        except asyncio.TimeoutError:
            pass


class JobManager:
    """Manages explanation jobs with an in-memory store."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    async def submit(
        self,
        document: str,
        task: TaskType,
        question: str | None,
        method: AttributionMethod,
        scalarizer: str,
    ) -> Job:
        job_id = uuid.uuid4().hex[:12]
        job = Job(
            id=job_id,
            document=document,
            task=task,
            question=question,
            method=method,
            scalarizer=scalarizer,
        )
        self._jobs[job_id] = job

        # Run the heavy work on the thread-pool, bridge progress back to asyncio
        loop = asyncio.get_running_loop()
        loop.run_in_executor(_executor, self._run_sync, job, loop)
        return job

    # ── synchronous worker (runs in thread) ──────────────────────────────

    def _run_sync(self, job: Job, loop: asyncio.EventLoop) -> None:
        """Blocking pipeline: generate → coarse explain → fine explain."""
        try:
            model = registry.get(job.task.value)

            def _progress(val: float) -> None:
                job.progress = val
                job.notify()

            # Step 1: Generate output
            job.status = JobStatus.generating
            job.notify()
            logger.info("[%s] Generating output", job.id)
            job.generated_output = generate_output(model, job.document, job.task)
            _progress(0.15)

            # Step 2: Coarse (sentence-level) explanation
            job.status = JobStatus.explaining_coarse
            job.notify()
            logger.info("[%s] Running coarse explanation", job.id)
            coarse = explain_coarse(
                model=model,
                document=job.document,
                generated_output=job.generated_output,
                task=job.task,
                question=job.question,
                method=job.method,
                scalarizer=job.scalarizer,
                on_progress=_progress,
            )
            job.attributions = coarse

            # Step 3: Fine (phrase/word-level) explanation
            job.status = JobStatus.explaining_fine
            job.notify()
            logger.info("[%s] Running fine explanation", job.id)
            refined = explain_fine(
                model=model,
                document=job.document,
                generated_output=job.generated_output,
                task=job.task,
                question=job.question,
                method=job.method,
                scalarizer=job.scalarizer,
                coarse_attributions=coarse,
                on_progress=_progress,
            )
            job.attributions = refined

            job.status = JobStatus.complete
            job.progress = 1.0
            job.notify()
            logger.info("[%s] Complete", job.id)

        except Exception:
            job.status = JobStatus.failed
            job.error = traceback.format_exc()
            job.notify()
            logger.exception("[%s] Failed", job.id)


# Singleton
job_manager = JobManager()
