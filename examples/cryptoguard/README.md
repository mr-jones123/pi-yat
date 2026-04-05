# CryptoGuard

**Vision-Language Model-Based Detection of Cryptocurrency Scams in Short-Form Videos**

CryptoGuard is a multimodal analysis system that detects cryptocurrency scams in short-form videos (TikTok, YouTube Shorts, Instagram Reels). It combines CLIP-based visual feature extraction, Whisper audio transcription, and Qwen3-VL vision-language reasoning to produce structured scam verdicts with chain-of-thought explanations.

## Architecture

```
URL → yt-dlp download → ┬→ Frame extraction → CLIP scam scoring ──┐
                         └→ Audio extraction → Whisper transcript ──┤
                                                                    ▼
                                              Qwen3-VL multimodal reasoning
                                                                    │
                                              Verdict + Confidence + Reasoning
```

## Key Features

- **Image Grid (IG-VLM):** Converts video into a single composite image (3×2 grid of 6 uniformly sampled frames) for VLM processing
- **CLIP Encoder:** Zero-shot scam indicator scoring via text-image similarity
- **Whisper Transcription:** Extracts spoken content for textual analysis
- **Qwen3-VL Reasoning:** Chain-of-thought multimodal analysis combining visual, textual, and CLIP signals
- **Web Interface:** Minimal React SPA for interactive analysis

## Requirements

- Python ≥ 3.11
- ffmpeg (system package)
- GPU with ≥8GB VRAM for local model inference (or use API mode)

## Installation

```bash
# Clone and install
cd cryptoguard
pip install -e ".[dev]"

# Or with uv
uv pip install -e ".[dev]"
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Two modes are supported:

- **Local mode:** Loads Qwen3-VL, CLIP, and Whisper models locally (requires GPU)
- **API mode:** Calls an OpenAI-compatible API endpoint (e.g., vLLM, Ollama)

## Usage

### CLI Demo

```bash
python demo.py "https://youtube.com/shorts/EXAMPLE"
```

### Web Application

```bash
# Start backend
python run.py

# In another terminal, start frontend
cd frontend && npm install && npm run dev
```

Then open `http://localhost:5173`.

### API

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/shorts/EXAMPLE"}'
```

## Testing

```bash
pytest tests/ -v
```

## Evaluation

```bash
python eval/evaluate.py --dataset eval/dataset.json
```

## Paper

```bash
cd paper && make
```

## Project Structure

```
cryptoguard/
├── cryptoguard/          # Core library
│   ├── config.py         # Settings and configuration
│   ├── models.py         # Pydantic data models
│   ├── video.py          # Video acquisition (yt-dlp)
│   ├── frames.py         # Frame extraction + CLIP encoder + image grid
│   ├── audio.py          # Audio extraction + Whisper transcription
│   ├── prompt.py         # Prompt templates for scam detection
│   ├── analyzer.py       # Qwen3-VL inference (local + API)
│   ├── pipeline.py       # Full analysis orchestration
│   └── api.py            # FastAPI endpoints
├── frontend/             # React SPA
├── tests/                # Test suite
├── eval/                 # Evaluation framework
├── paper/                # LaTeX paper
├── demo.py               # CLI demo script
└── run.py                # Server entry point
```

## Citation

If you use CryptoGuard in your research, please cite:

```bibtex
@article{cryptoguard2026,
  title={CryptoGuard: Vision-Language Model-Based Detection of Cryptocurrency Scams in Short-Form Videos},
  year={2026}
}
```

## License

MIT
