"""Model loading and lifecycle management.

Loads HuggingFace models once at startup and exposes them via a singleton.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from icx360.utils.model_wrappers import HFModel

from app.config import settings

logger = logging.getLogger(__name__)


def _resolve_device() -> str:
    if settings.device == "auto":
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    return settings.device


@dataclass
class ModelRegistry:
    """Holds loaded models keyed by task name."""

    device: str = field(default_factory=_resolve_device)
    _models: dict[str, HFModel] = field(default_factory=dict)
    _loaded: bool = False

    # ── public ───────────────────────────────────────────────────────────

    def load_all(self) -> None:
        """Eagerly load all configured models (called once at startup)."""
        if self._loaded:
            return

        logger.info("Loading summarization model: %s on %s", settings.summarization_model, self.device)
        self._models["summarization"] = self._load_hf(settings.summarization_model)

        logger.info("Loading QA model: %s on %s", settings.qa_model, self.device)
        self._models["question_answering"] = self._load_hf(settings.qa_model)

        self._loaded = True
        logger.info("All models loaded successfully.")

    def get(self, task: str) -> HFModel:
        if not self._loaded:
            raise RuntimeError("Models not loaded. Call load_all() first.")
        model = self._models.get(task)
        if model is None:
            raise KeyError(f"No model loaded for task '{task}'")
        return model

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ── private ──────────────────────────────────────────────────────────

    def _load_hf(self, model_id: str) -> HFModel:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
        model = model.to(self.device)
        model.eval()

        # Ensure pad token is set (needed for batched generation)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        return HFModel(model=model, tokenizer=tokenizer)


# Singleton instance
registry = ModelRegistry()
