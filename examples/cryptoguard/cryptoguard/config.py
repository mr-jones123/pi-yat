"""Application configuration via environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # VLM configuration
    vlm_mode: str = "api"  # "local" or "api"
    vlm_model_id: str = "Qwen/Qwen3-VL-7B-Instruct"
    vlm_api_base: str = "http://localhost:8080/v1"
    vlm_api_key: str = "not-needed"

    # CLIP encoder
    clip_model_id: str = "openai/clip-vit-base-patch32"

    # Whisper transcription
    whisper_model_id: str = "openai/whisper-base"

    # Frame extraction
    n_frames: int = 6
    grid_cols: int = 3
    frame_size: int = 384

    # Video constraints
    max_video_duration: int = 180  # seconds

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Temp directory
    temp_dir: Path = Path("/tmp/cryptoguard")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def ensure_temp_dir(self) -> Path:
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        return self.temp_dir
