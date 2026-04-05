"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- API ---
    app_title: str = "MExGen API"
    app_version: str = "1.0.0"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # --- Model ---
    # Summarization model (HuggingFace model ID)
    summarization_model: str = "sshleifer/distilbart-xsum-12-6"
    # QA model (HuggingFace model ID)
    qa_model: str = "google/flan-t5-base"
    # Device: "auto" picks GPU if available, else CPU
    device: str = "auto"

    # --- MExGen defaults ---
    scalarizer: str = "prob"  # "prob" (log-prob, needs logits) or "text" (text-only similarity)
    text_scalarizers: list[str] = ["bert"]  # used when scalarizer="text"
    attribution_method: str = "clime"  # "clime", "lshap", or "loo"
    spacy_model: str = "en_core_web_sm"  # "en_core_web_sm" or "en_core_web_trf"

    # --- C-LIME defaults ---
    oversampling_factor: int = 10
    max_units_replace: int = 2

    # --- Multi-level ---
    top_k_refine: int = 3
    refine_threshold: float = 0.33

    model_config = {"env_prefix": "MEXGEN_", "env_file": ".env"}


settings = Settings()
