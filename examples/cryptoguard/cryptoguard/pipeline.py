"""Orchestrates the full CryptoGuard analysis pipeline."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from cryptoguard.analyzer import QwenAnalyzer
from cryptoguard.audio import WhisperTranscriber, extract_audio
from cryptoguard.config import Settings
from cryptoguard.frames import CLIPEncoder, build_image_grid, extract_frames
from cryptoguard.models import AnalysisResponse, AnalysisResult, Verdict
from cryptoguard.prompt import SCAM_INDICATOR_PROMPTS
from cryptoguard.video import VideoDownloadError, download_video

logger = logging.getLogger(__name__)


class CryptoGuardPipeline:
    """End-to-end pipeline: URL → download → extract → analyse → result."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self._clip: CLIPEncoder | None = None
        self._whisper: WhisperTranscriber | None = None
        self._analyzer: QwenAnalyzer | None = None

    # Lazy init so we only load heavy models when first needed
    @property
    def clip(self) -> CLIPEncoder:
        if self._clip is None:
            self._clip = CLIPEncoder(self.settings.clip_model_id)
        return self._clip

    @property
    def whisper(self) -> WhisperTranscriber:
        if self._whisper is None:
            self._whisper = WhisperTranscriber(self.settings.whisper_model_id)
        return self._whisper

    @property
    def analyzer(self) -> QwenAnalyzer:
        if self._analyzer is None:
            self._analyzer = QwenAnalyzer(self.settings)
        return self._analyzer

    async def analyze_url(self, url: str) -> AnalysisResponse:
        """Run the full pipeline on a video URL."""
        t0 = time.time()

        # 1. Download video
        logger.info("Downloading %s", url)
        try:
            video_path = download_video(url, self.settings)
        except VideoDownloadError as exc:
            return AnalysisResponse(
                url=url,
                result=AnalysisResult(
                    verdict=Verdict.UNCERTAIN,
                    confidence=0.0,
                    reasoning=f"Download failed: {exc}",
                ),
                duration_seconds=time.time() - t0,
            )

        try:
            result, grid_b64 = await self._process_video(video_path)
        finally:
            # Clean up downloaded file
            video_path.unlink(missing_ok=True)

        return AnalysisResponse(
            url=url,
            result=result,
            image_grid_b64=grid_b64,
            duration_seconds=time.time() - t0,
        )

    async def _process_video(self, video_path: Path) -> tuple[AnalysisResult, str]:
        import base64
        from io import BytesIO

        # 2a. Extract frames and build image grid
        logger.info("Extracting frames ...")
        frames = extract_frames(video_path, self.settings.n_frames)
        grid = build_image_grid(frames, self.settings.grid_cols, self.settings.frame_size)

        # Encode grid as base64 for frontend
        buf = BytesIO()
        grid.save(buf, format="PNG")
        grid_b64 = base64.b64encode(buf.getvalue()).decode()

        # 2b. CLIP scam indicator scoring
        logger.info("Running CLIP scam indicator scoring ...")
        clip_scores = self.clip.score_scam_indicators(frames, SCAM_INDICATOR_PROMPTS)

        # 2c. Audio extraction and transcription
        logger.info("Transcribing audio ...")
        try:
            audio_path = extract_audio(video_path)
            transcript = self.whisper.transcribe(audio_path)
            Path(audio_path).unlink(missing_ok=True)
        except Exception as exc:
            logger.warning("Audio extraction/transcription failed: %s", exc)
            transcript = ""

        # 3. VLM analysis
        logger.info("Running Qwen3-VL analysis ...")
        result = await self.analyzer.analyze(grid, transcript, clip_scores)

        # Merge CLIP scores into the result
        result.transcript = transcript
        result.clip_scores = clip_scores

        return result, grid_b64
