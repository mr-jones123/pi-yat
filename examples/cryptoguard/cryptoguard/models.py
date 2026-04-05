"""Pydantic data models for request/response schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    SCAM = "scam"
    LEGITIMATE = "legitimate"
    UNCERTAIN = "uncertain"


class ScamIndicator(BaseModel):
    """A single scam indicator detected by CLIP or VLM."""

    name: str = Field(description="Short name of the indicator")
    score: float = Field(ge=0.0, le=1.0, description="Confidence 0-1")
    source: str = Field(description="Detection source: 'clip' or 'vlm'")


class AnalysisResult(BaseModel):
    """Structured output from the analysis pipeline."""

    verdict: Verdict
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(description="Chain-of-thought explanation")
    indicators: list[ScamIndicator] = Field(default_factory=list)
    transcript: str = Field(default="")
    clip_scores: dict[str, float] = Field(default_factory=dict)


class AnalysisRequest(BaseModel):
    """API request to analyze a video URL."""

    url: str = Field(description="URL of the short-form video")


class AnalysisResponse(BaseModel):
    """Full API response including metadata."""

    url: str
    result: AnalysisResult
    image_grid_b64: str = Field(default="", description="Base64-encoded image grid PNG")
    duration_seconds: float = Field(default=0.0)
