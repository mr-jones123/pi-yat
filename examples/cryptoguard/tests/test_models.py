"""Tests for Pydantic data models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from cryptoguard.models import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisResult,
    ScamIndicator,
    Verdict,
)


class TestVerdict:
    def test_enum_values(self):
        assert Verdict.SCAM.value == "scam"
        assert Verdict.LEGITIMATE.value == "legitimate"
        assert Verdict.UNCERTAIN.value == "uncertain"


class TestScamIndicator:
    def test_valid_indicator(self):
        ind = ScamIndicator(name="fake profit", score=0.85, source="clip")
        assert ind.name == "fake profit"
        assert ind.score == 0.85

    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            ScamIndicator(name="x", score=1.5, source="clip")
        with pytest.raises(ValidationError):
            ScamIndicator(name="x", score=-0.1, source="vlm")


class TestAnalysisResult:
    def test_minimal_result(self):
        r = AnalysisResult(
            verdict=Verdict.SCAM,
            confidence=0.95,
            reasoning="High confidence scam",
        )
        assert r.verdict == Verdict.SCAM
        assert r.indicators == []
        assert r.transcript == ""

    def test_full_result(self):
        r = AnalysisResult(
            verdict=Verdict.LEGITIMATE,
            confidence=0.7,
            reasoning="Appears to be educational content",
            indicators=[ScamIndicator(name="test", score=0.1, source="vlm")],
            transcript="This is how mining works",
            clip_scores={"countdown": 0.2},
        )
        assert len(r.indicators) == 1
        assert r.clip_scores["countdown"] == 0.2

    def test_serialization_roundtrip(self):
        r = AnalysisResult(
            verdict=Verdict.UNCERTAIN,
            confidence=0.5,
            reasoning="Mixed signals",
        )
        data = r.model_dump()
        r2 = AnalysisResult(**data)
        assert r == r2


class TestAnalysisRequest:
    def test_valid_url(self):
        req = AnalysisRequest(url="https://youtube.com/shorts/abc123")
        assert req.url.startswith("https")


class TestAnalysisResponse:
    def test_full_response(self):
        resp = AnalysisResponse(
            url="https://example.com/video",
            result=AnalysisResult(
                verdict=Verdict.SCAM,
                confidence=0.9,
                reasoning="Definite scam",
            ),
            image_grid_b64="aGVsbG8=",
            duration_seconds=3.5,
        )
        assert resp.duration_seconds == 3.5
        assert resp.result.verdict == Verdict.SCAM
