"""Audio extraction and Whisper transcription."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


class AudioExtractionError(Exception):
    pass


def extract_audio(video_path: str | Path, output_path: str | Path | None = None) -> Path:
    """Extract mono 16 kHz WAV audio from a video using ffmpeg."""
    if output_path is None:
        fd, tmp = tempfile.mkstemp(suffix=".wav")
        import os
        os.close(fd)
        output_path = Path(tmp)
    else:
        output_path = Path(output_path)

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(output_path),
        "-y",
        "-loglevel", "error",
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=60, check=True)
    except FileNotFoundError as exc:
        raise AudioExtractionError(
            "ffmpeg not found. Install it: https://ffmpeg.org/download.html"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise AudioExtractionError(
            f"ffmpeg failed: {exc.stderr.decode() if exc.stderr else 'unknown'}"
        ) from exc

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise AudioExtractionError("Audio extraction produced empty file")

    return output_path


class WhisperTranscriber:
    """Whisper-based speech-to-text using HuggingFace transformers pipeline."""

    def __init__(self, model_id: str = "openai/whisper-base"):
        import torch
        from transformers import pipeline

        device = 0 if torch.cuda.is_available() else -1
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=model_id,
            chunk_length_s=30,
            device=device,
        )

    def transcribe(self, audio_path: str | Path) -> str:
        """Transcribe an audio file and return the full text."""
        result = self.pipe(str(audio_path))
        if isinstance(result, dict):
            return result.get("text", "").strip()
        return ""
