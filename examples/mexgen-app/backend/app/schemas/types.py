"""Pydantic models for API request/response schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────


class TaskType(str, Enum):
    summarization = "summarization"
    question_answering = "question_answering"


class JobStatus(str, Enum):
    pending = "pending"
    generating = "generating"  # LLM is producing the output
    explaining_coarse = "explaining_coarse"  # sentence-level attribution
    explaining_fine = "explaining_fine"  # phrase/word-level attribution
    complete = "complete"
    failed = "failed"


class AttributionMethod(str, Enum):
    clime = "clime"
    lshap = "lshap"
    loo = "loo"


# ── Request ──────────────────────────────────────────────────────────────────


class ExplainRequest(BaseModel):
    """Submit a document for explanation."""

    document: str = Field(..., min_length=10, max_length=50_000, description="Input context (article, passage, etc.)")
    task: TaskType = Field(default=TaskType.summarization)
    question: str | None = Field(default=None, description="Required for QA task")
    method: AttributionMethod = Field(default=AttributionMethod.clime)
    scalarizer: str = Field(default="prob", description="'prob' for log-prob or 'text' for text-similarity")


class RefineRequest(BaseModel):
    """Request drill-down on a specific unit."""

    job_id: str
    unit_index: int = Field(..., ge=0, description="Index of unit to refine")


# ── Response ─────────────────────────────────────────────────────────────────


class UnitAttribution(BaseModel):
    """A single unit with its attribution score."""

    text: str
    unit_type: str  # "s" sentence, "ph" phrase, "w" word, "n" not attributed
    score: float
    index: int
    children: list[UnitAttribution] | None = None  # finer-level attributions after drill-down


class ExplainResponse(BaseModel):
    """Full explanation result."""

    job_id: str
    status: JobStatus
    task: TaskType
    document: str
    question: str | None = None
    generated_output: str | None = None
    attributions: list[UnitAttribution] = []
    progress: float = 0.0  # 0.0 to 1.0
    error: str | None = None


class JobStatusResponse(BaseModel):
    """Lightweight status check."""

    job_id: str
    status: JobStatus
    progress: float = 0.0


class HealthResponse(BaseModel):
    status: str = "ok"
    models_loaded: bool = False
    device: str = "cpu"
