"""REST API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.jobs import job_manager
from app.core.models import registry
from app.schemas.types import (
    ExplainRequest,
    ExplainResponse,
    HealthResponse,
    JobStatusResponse,
    TaskType,
)

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        models_loaded=registry.is_loaded,
        device=registry.device,
    )


@router.post("/explain", response_model=ExplainResponse)
async def explain(req: ExplainRequest) -> ExplainResponse:
    """Submit a document for explanation. Returns immediately with a job_id."""
    if req.task == TaskType.question_answering and not req.question:
        raise HTTPException(status_code=422, detail="Question is required for QA task")

    job = await job_manager.submit(
        document=req.document,
        task=req.task,
        question=req.question,
        method=req.method,
        scalarizer=req.scalarizer,
    )
    return job.to_response()


@router.get("/jobs/{job_id}", response_model=ExplainResponse)
async def get_job(job_id: str) -> ExplainResponse:
    """Poll for job status and results."""
    job = job_manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_response()


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Lightweight status check (no attribution payload)."""
    job = job_manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(job_id=job.id, status=job.status, progress=job.progress)
