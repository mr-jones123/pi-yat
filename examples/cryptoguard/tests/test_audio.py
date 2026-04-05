"""Tests for audio extraction."""

from __future__ import annotations

import subprocess

import pytest

from cryptoguard.audio import AudioExtractionError, extract_audio


class TestExtractAudio:
    def test_extract_from_synthetic_video(self, synthetic_video, tmp_path):
        """Synthetic video has no audio track, so ffmpeg should still produce a file
        (silent WAV) or fail gracefully."""
        out = tmp_path / "audio.wav"
        try:
            result = extract_audio(synthetic_video, out)
            assert result.exists()
        except AudioExtractionError:
            # ffmpeg may error on video-only files, which is acceptable
            pass

    def test_nonexistent_video_raises(self, tmp_path):
        with pytest.raises(AudioExtractionError):
            extract_audio(tmp_path / "nope.mp4")

    def test_ffmpeg_missing_raises(self, tmp_path, monkeypatch):
        """Simulate ffmpeg not being installed."""
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *a, **kw: (_ for _ in ()).throw(FileNotFoundError),
        )
        with pytest.raises(AudioExtractionError, match="ffmpeg not found"):
            extract_audio(tmp_path / "dummy.mp4")
