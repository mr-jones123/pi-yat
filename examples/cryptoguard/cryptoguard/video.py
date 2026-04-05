"""Video acquisition via yt-dlp."""

from __future__ import annotations

import json
import subprocess
import uuid
from pathlib import Path

from cryptoguard.config import Settings


class VideoDownloadError(Exception):
    pass


def download_video(url: str, settings: Settings) -> Path:
    """Download a short-form video and return the local file path.

    Validates duration against settings.max_video_duration.
    """
    out_dir = settings.ensure_temp_dir()
    filename = f"{uuid.uuid4().hex}.mp4"
    out_path = out_dir / filename

    # Probe duration first
    probe_cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-download",
        url,
    ]
    try:
        probe = subprocess.run(
            probe_cmd, capture_output=True, text=True, timeout=30, check=True
        )
        meta = json.loads(probe.stdout)
        duration = meta.get("duration", 0)
        if duration and duration > settings.max_video_duration:
            raise VideoDownloadError(
                f"Video too long ({duration}s > {settings.max_video_duration}s)"
            )
    except subprocess.CalledProcessError as exc:
        raise VideoDownloadError(f"Failed to probe video: {exc.stderr}") from exc
    except (json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        raise VideoDownloadError(f"Failed to probe video metadata: {exc}") from exc

    # Download
    dl_cmd = [
        "yt-dlp",
        "-f", "mp4/best[ext=mp4]",
        "-o", str(out_path),
        "--no-playlist",
        "--quiet",
        url,
    ]
    try:
        subprocess.run(dl_cmd, capture_output=True, timeout=120, check=True)
    except subprocess.CalledProcessError as exc:
        raise VideoDownloadError(
            f"Download failed: {exc.stderr.decode() if exc.stderr else 'unknown error'}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise VideoDownloadError("Download timed out") from exc

    if not out_path.exists():
        raise VideoDownloadError("Downloaded file not found")

    return out_path
