"""Tests for the analysis pipeline with mocked components."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cryptoguard.models import AnalysisResult, Verdict
from cryptoguard.pipeline import CryptoGuardPipeline


@pytest.fixture
def mock_pipeline(settings, synthetic_video):
    """Pipeline with all heavy components mocked."""
    pipe = CryptoGuardPipeline(settings)

    # Mock CLIP
    mock_clip = MagicMock()
    mock_clip.score_scam_indicators.return_value = {
        "fake profit screenshot": 0.8,
        "countdown timer": 0.3,
    }
    pipe._clip = mock_clip

    # Mock Whisper
    mock_whisper = MagicMock()
    mock_whisper.transcribe.return_value = "Send BTC to this wallet for 10x returns!"
    pipe._whisper = mock_whisper

    # Mock Analyzer
    mock_analyzer = MagicMock()
    mock_analyzer.analyze = AsyncMock(
        return_value=AnalysisResult(
            verdict=Verdict.SCAM,
            confidence=0.92,
            reasoning="Multiple scam indicators detected.",
        )
    )
    pipe._analyzer = mock_analyzer

    return pipe


class TestPipelineIntegration:
    @pytest.mark.asyncio
    async def test_process_video(self, mock_pipeline, synthetic_video):
        with patch("cryptoguard.pipeline.extract_audio") as mock_ea:
            mock_ea.return_value = "/tmp/fake.wav"
            result, grid_b64 = await mock_pipeline._process_video(synthetic_video)
        assert result.verdict == Verdict.SCAM
        assert result.confidence == 0.92
        assert len(grid_b64) > 0  # base64 encoded image
        assert result.transcript == "Send BTC to this wallet for 10x returns!"

    @pytest.mark.asyncio
    async def test_process_video_calls_clip(self, mock_pipeline, synthetic_video):
        with patch("cryptoguard.pipeline.extract_audio") as mock_ea:
            mock_ea.return_value = "/tmp/fake.wav"
            await mock_pipeline._process_video(synthetic_video)
        mock_pipeline._clip.score_scam_indicators.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_video_calls_whisper(self, mock_pipeline, synthetic_video):
        with patch("cryptoguard.pipeline.extract_audio") as mock_ea:
            mock_ea.return_value = "/tmp/fake.wav"
            await mock_pipeline._process_video(synthetic_video)
        mock_pipeline._whisper.transcribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_video_calls_analyzer(self, mock_pipeline, synthetic_video):
        with patch("cryptoguard.pipeline.extract_audio") as mock_ea:
            mock_ea.return_value = "/tmp/fake.wav"
            await mock_pipeline._process_video(synthetic_video)
        mock_pipeline._analyzer.analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_url_bad_url(self, mock_pipeline):
        """A bad URL should return UNCERTAIN, not raise."""
        with patch("cryptoguard.pipeline.download_video") as mock_dl:
            from cryptoguard.video import VideoDownloadError

            mock_dl.side_effect = VideoDownloadError("fail")
            resp = await mock_pipeline.analyze_url("https://bad.url/x")
            assert resp.result.verdict == Verdict.UNCERTAIN
            assert "Download failed" in resp.result.reasoning
