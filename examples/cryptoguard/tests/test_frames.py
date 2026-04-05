"""Tests for frame extraction and image grid construction."""

from __future__ import annotations


import pytest
from PIL import Image

from cryptoguard.frames import build_image_grid, extract_frames


class TestExtractFrames:
    def test_extracts_correct_count(self, synthetic_video):
        frames = extract_frames(synthetic_video, n_frames=6)
        assert len(frames) == 6

    def test_frames_are_pil_images(self, synthetic_video):
        frames = extract_frames(synthetic_video, n_frames=4)
        for f in frames:
            assert isinstance(f, Image.Image)
            assert f.mode == "RGB"

    def test_different_n_frames(self, synthetic_video):
        for n in [1, 3, 6, 9]:
            frames = extract_frames(synthetic_video, n_frames=n)
            assert len(frames) == n

    def test_invalid_path_raises(self, tmp_path):
        with pytest.raises(ValueError):
            extract_frames(tmp_path / "nonexistent.mp4")


class TestBuildImageGrid:
    def test_grid_dimensions_6_frames(self, sample_frames):
        grid = build_image_grid(sample_frames, grid_cols=3, frame_size=128)
        assert grid.size == (3 * 128, 2 * 128)  # 384×256

    def test_grid_dimensions_4_frames(self):
        frames = [Image.new("RGB", (100, 100), "red") for _ in range(4)]
        grid = build_image_grid(frames, grid_cols=2, frame_size=64)
        assert grid.size == (2 * 64, 2 * 64)

    def test_grid_dimensions_9_frames(self):
        frames = [Image.new("RGB", (100, 100), "blue") for _ in range(9)]
        grid = build_image_grid(frames, grid_cols=3, frame_size=100)
        assert grid.size == (300, 300)

    def test_grid_single_frame(self):
        frames = [Image.new("RGB", (200, 200), "green")]
        grid = build_image_grid(frames, grid_cols=3, frame_size=128)
        # 1 frame in a 3-col grid → 1 row
        assert grid.size == (3 * 128, 1 * 128)

    def test_grid_is_rgb(self, sample_frames):
        grid = build_image_grid(sample_frames, grid_cols=3, frame_size=64)
        assert grid.mode == "RGB"

    def test_grid_preserves_content(self):
        """Top-left cell should contain the first frame's colour."""
        frames = [
            Image.new("RGB", (50, 50), (255, 0, 0)),
            Image.new("RGB", (50, 50), (0, 255, 0)),
        ]
        grid = build_image_grid(frames, grid_cols=2, frame_size=50)
        # Sample top-left pixel → should be red
        assert grid.getpixel((5, 5)) == (255, 0, 0)
        # Sample top-right cell pixel → should be green
        assert grid.getpixel((55, 5)) == (0, 255, 0)
