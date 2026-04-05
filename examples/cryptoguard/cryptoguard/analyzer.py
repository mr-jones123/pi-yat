"""Qwen3-VL analysis module with local and API backends."""

from __future__ import annotations

import base64
import json
import logging
import re
from io import BytesIO
from typing import TYPE_CHECKING

from cryptoguard.models import AnalysisResult, ScamIndicator, Verdict
from cryptoguard.prompt import SYSTEM_PROMPT, build_analysis_prompt

if TYPE_CHECKING:
    from PIL import Image

    from cryptoguard.config import Settings

logger = logging.getLogger(__name__)


def _image_to_b64(image: Image.Image) -> str:
    buf = BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _parse_vlm_response(raw: str) -> AnalysisResult:
    """Extract JSON from the VLM response and parse into AnalysisResult."""
    # Try to find JSON block in the response
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not json_match:
        logger.warning("No JSON found in VLM response, returning uncertain")
        return AnalysisResult(
            verdict=Verdict.UNCERTAIN,
            confidence=0.0,
            reasoning=f"Could not parse VLM response: {raw[:500]}",
        )

    try:
        data = json.loads(json_match.group())
    except json.JSONDecodeError:
        return AnalysisResult(
            verdict=Verdict.UNCERTAIN,
            confidence=0.0,
            reasoning=f"Invalid JSON in VLM response: {raw[:500]}",
        )

    indicators = [
        ScamIndicator(**ind) for ind in data.get("indicators", [])
    ]
    return AnalysisResult(
        verdict=Verdict(data.get("verdict", "uncertain")),
        confidence=float(data.get("confidence", 0.0)),
        reasoning=data.get("reasoning", ""),
        indicators=indicators,
    )


class QwenAnalyzer:
    """Analyse an image grid + transcript using Qwen3-VL.

    Supports two modes:
    - **local**: loads the model via HuggingFace transformers (needs GPU).
    - **api**: calls an OpenAI-compatible chat completions endpoint
      (works with vLLM, Ollama, etc.).
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._model = None
        self._processor = None

        if settings.vlm_mode == "local":
            self._load_local()

    # ------------------------------------------------------------------
    # Local model
    # ------------------------------------------------------------------

    def _load_local(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoProcessor

        logger.info("Loading %s locally ...", self.settings.vlm_model_id)
        self._processor = AutoProcessor.from_pretrained(
            self.settings.vlm_model_id,
            trust_remote_code=True,
        )
        self._model = AutoModelForCausalLM.from_pretrained(
            self.settings.vlm_model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )
        self._model.eval()
        logger.info("Model loaded.")

    def _analyze_local(
        self,
        image_grid: Image.Image,
        transcript: str,
        clip_scores: dict[str, float],
    ) -> AnalysisResult:
        import torch

        assert self._model is not None and self._processor is not None

        user_prompt = build_analysis_prompt(transcript, clip_scores)
        messages = [
            {"role": "system", "content": [{"type": "text", "text": SYSTEM_PROMPT}]},
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image_grid},
                    {"type": "text", "text": user_prompt},
                ],
            },
        ]

        text = self._processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._processor(
            text=[text], images=[image_grid], return_tensors="pt"
        ).to(self._model.device)

        with torch.no_grad():
            ids = self._model.generate(**inputs, max_new_tokens=1024, temperature=0.1)
        raw = self._processor.batch_decode(
            ids[:, inputs["input_ids"].shape[1] :], skip_special_tokens=True
        )[0]

        return _parse_vlm_response(raw)

    # ------------------------------------------------------------------
    # API model (OpenAI-compatible)
    # ------------------------------------------------------------------

    async def _analyze_api(
        self,
        image_grid: Image.Image,
        transcript: str,
        clip_scores: dict[str, float],
    ) -> AnalysisResult:
        import httpx

        img_b64 = _image_to_b64(image_grid)
        user_prompt = build_analysis_prompt(transcript, clip_scores)

        payload = {
            "model": self.settings.vlm_model_id,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                        },
                        {"type": "text", "text": user_prompt},
                    ],
                },
            ],
            "max_tokens": 1024,
            "temperature": 0.1,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.settings.vlm_api_base}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.settings.vlm_api_key}"},
            )
            resp.raise_for_status()

        data = resp.json()
        raw = data["choices"][0]["message"]["content"]
        return _parse_vlm_response(raw)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def analyze(
        self,
        image_grid: Image.Image,
        transcript: str,
        clip_scores: dict[str, float],
    ) -> AnalysisResult:
        """Run VLM analysis and return a structured result."""
        if self.settings.vlm_mode == "local":
            return self._analyze_local(image_grid, transcript, clip_scores)
        return await self._analyze_api(image_grid, transcript, clip_scores)
