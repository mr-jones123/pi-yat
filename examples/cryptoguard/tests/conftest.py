"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image

from cryptoguard.config import Settings


@pytest.fixture
def settings(tmp_path):
    """Settings pointed at a temp directory, using API mode to avoid loading models."""
    return Settings(
        vlm_mode="api",
        vlm_api_base="http://localhost:9999/v1",
        temp_dir=tmp_path / "cg_tmp",
        n_frames=6,
        grid_cols=3,
        frame_size=128,  # smaller for tests
    )


@pytest.fixture
def synthetic_video(tmp_path) -> Path:
    """Create a short synthetic MP4 video (30 frames, solid colour changing)."""
    out = tmp_path / "test_video.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out), fourcc, 10.0, (320, 240))

    for i in range(30):
        # Gradient from blue to red across frames
        frame = np.full((240, 320, 3), fill_value=0, dtype=np.uint8)
        frame[:, :, 0] = int(255 * i / 29)  # blue channel
        frame[:, :, 2] = int(255 * (29 - i) / 29)  # red channel
        writer.write(frame)

    writer.release()
    assert out.exists()
    return out


@pytest.fixture
def sample_frames() -> list[Image.Image]:
    """Six solid-colour PIL images for grid tests."""
    colours = ["red", "green", "blue", "yellow", "cyan", "magenta"]
    return [Image.new("RGB", (320, 240), c) for c in colours]
