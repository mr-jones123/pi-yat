"""Tests for FastAPI endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from cryptoguard.models import AnalysisResponse, AnalysisResult, Verdict


@pytest.fixture
def client():
    """TestClient with the pipeline mocked out."""
    mock_result = AnalysisResponse(
        url="https://example.com/video",
        result=AnalysisResult(
            verdict=Verdict.SCAM,
            confidence=0.9,
            reasoning="Scam detected",
            transcript="send btc now",
            clip_scores={"fake profit": 0.8},
        ),
        image_grid_b64="dGVzdA==",
        duration_seconds=2.5,
    )

    with patch("cryptoguard.api.pipeline") as mock_pipe:
        mock_pipe.analyze_url = AsyncMock(return_value=mock_result)
        from cryptoguard.api import app

        yield TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestAnalyzeEndpoint:
    def test_analyze_returns_result(self, client):
        resp = client.post(
            "/api/analyze",
            json={"url": "https://youtube.com/shorts/abc123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"]["verdict"] == "scam"
        assert data["result"]["confidence"] == 0.9
        assert data["duration_seconds"] == 2.5

    def test_analyze_empty_url_rejected(self, client):
        resp = client.post("/api/analyze", json={"url": ""})
        assert resp.status_code == 400

    def test_analyze_missing_url_rejected(self, client):
        resp = client.post("/api/analyze", json={})
        assert resp.status_code == 422  # Pydantic validation error

    def test_analyze_response_has_image_grid(self, client):
        resp = client.post(
            "/api/analyze",
            json={"url": "https://example.com/v"},
        )
        data = resp.json()
        assert "image_grid_b64" in data
        assert len(data["image_grid_b64"]) > 0
