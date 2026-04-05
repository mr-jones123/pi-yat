"""Frame extraction, image grid construction, and CLIP encoding."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import cv2
import numpy as np
import torch
from PIL import Image

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Frame extraction
# ---------------------------------------------------------------------------

def extract_frames(video_path: str | Path, n_frames: int = 6) -> list[Image.Image]:
    """Uniformly sample *n_frames* from a video file.

    Following the IG-VLM methodology (Kim et al., 2024), frames are sampled
    at uniform intervals across the video duration.
    """
    cap = cv2.VideoCapture(str(video_path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total == 0:
        cap.release()
        raise ValueError(f"Cannot read frames from {video_path}")

    indices = np.linspace(0, total - 1, n_frames, dtype=int)
    frames: list[Image.Image] = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ret, bgr = cap.read()
        if ret:
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            frames.append(Image.fromarray(rgb))
    cap.release()

    if len(frames) == 0:
        raise ValueError("No frames could be extracted")
    return frames


# ---------------------------------------------------------------------------
# Image grid construction (IG-VLM approach)
# ---------------------------------------------------------------------------

def build_image_grid(
    frames: list[Image.Image],
    grid_cols: int = 3,
    frame_size: int = 384,
) -> Image.Image:
    """Arrange frames in a grid layout and return a single composite image.

    For 6 frames with grid_cols=3: produces a 3×2 grid (1152×768 px).
    This follows Kim et al., 2024 which showed square-ish grids
    with row-major ordering yield the best VLM performance.
    """
    n = len(frames)
    grid_rows = math.ceil(n / grid_cols)
    cell = (frame_size, frame_size)
    grid_w = grid_cols * cell[0]
    grid_h = grid_rows * cell[1]
    grid = Image.new("RGB", (grid_w, grid_h), color=(0, 0, 0))

    for i, frame in enumerate(frames):
        row, col = divmod(i, grid_cols)
        resized = frame.resize(cell, Image.LANCZOS)
        grid.paste(resized, (col * cell[0], row * cell[1]))

    return grid


# ---------------------------------------------------------------------------
# CLIP encoder for zero-shot scam indicator scoring
# ---------------------------------------------------------------------------

class CLIPEncoder:
    """Wraps a CLIP model (from HuggingFace transformers) for zero-shot
    visual scam indicator scoring.

    Uses cosine similarity between frame embeddings and scam-indicative
    text descriptions to produce per-indicator scores.
    """

    def __init__(self, model_id: str = "openai/clip-vit-base-patch32"):
        from transformers import CLIPModel, CLIPProcessor

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = CLIPModel.from_pretrained(model_id).to(self.device).eval()
        self.processor = CLIPProcessor.from_pretrained(model_id)

    @torch.no_grad()
    def encode_frames(self, frames: list[Image.Image]) -> torch.Tensor:
        """Return L2-normalised image embeddings of shape (N, D)."""
        inputs = self.processor(images=frames, return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        feats = self.model.get_image_features(**inputs)
        return feats / feats.norm(dim=-1, keepdim=True)

    @torch.no_grad()
    def encode_texts(self, texts: list[str]) -> torch.Tensor:
        """Return L2-normalised text embeddings of shape (T, D)."""
        inputs = self.processor(text=texts, return_tensors="pt", padding=True, truncation=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        feats = self.model.get_text_features(**inputs)
        return feats / feats.norm(dim=-1, keepdim=True)

    def score_scam_indicators(
        self,
        frames: list[Image.Image],
        indicator_prompts: list[str],
    ) -> dict[str, float]:
        """Compute max cosine similarity between frames and each indicator.

        Returns a dict mapping indicator prompt → highest similarity score
        across all frames.  Scores are in [0, 1] after clamping.
        """
        img_emb = self.encode_frames(frames)     # (N, D)
        txt_emb = self.encode_texts(indicator_prompts)  # (T, D)
        sims = (img_emb @ txt_emb.T)              # (N, T)
        max_sims = sims.max(dim=0).values          # (T,)
        return {
            prompt: round(max_sims[i].clamp(0, 1).item(), 4)
            for i, prompt in enumerate(indicator_prompts)
        }
