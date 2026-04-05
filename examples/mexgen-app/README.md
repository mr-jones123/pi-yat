# MExGen — Multi-Level Explanations for Generative Language Models

A production web application for explaining LLM outputs through input attribution.
Given a document and a task (summarization or QA), the app generates the LLM's response
and highlights which parts of the input context drove that response, with interactive
drill-down from sentences to phrases to words.

Based on the [MExGen paper](https://arxiv.org/abs/2403.14459) (Paes, Wei et al., ACL 2025)
and the [ICX360 toolkit](https://github.com/IBM/ICX360).

## Architecture

```
┌─────────────┐        ┌──────────────────────────┐
│  React UI   │──REST──▶  FastAPI Backend          │
│  (Vite)     │◀──WS───│                          │
│             │        │  ┌──────────────────────┐ │
│ • Doc input │        │  │  icx360 / MExGen     │ │
│ • Task pick │        │  │  • C-LIME / L-SHAP   │ │
│ • Highlight │        │  │  • Multi-level segm. │ │
│ • Drilldown │        │  │  • Scalarizers        │ │
└─────────────┘        │  └──────────────────────┘ │
                       │  ┌──────────────────────┐ │
                       │  │  HuggingFace Models   │ │
                       │  │  • DistilBART (summ)  │ │
                       │  │  • Flan-T5 (QA)       │ │
                       │  └──────────────────────┘ │
                       └──────────────────────────┘
```

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+, [uv](https://docs.astral.sh/uv/)
- Node.js 20+

### Backend

```bash
cd backend
uv venv --python 3.12
source .venv/bin/activate
uv pip install .
python -m spacy download en_core_web_sm

# Start the API server
uvicorn app.main:app --reload --port 8000
```

On first run, HuggingFace models will be downloaded (~1.5 GB).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The Vite dev server proxies `/api` and `/ws` to the backend.

## Docker

```bash
docker compose up --build
```

Frontend at **http://localhost:3000**, API at **http://localhost:8000**.

## Usage

1. Select a task: **Summarization** or **Question Answering**
2. Paste your document (or click "Load sample")
3. Pick an attribution method (C-LIME recommended) and scalarizer
4. Click **Explain**
5. Watch real-time progress as the pipeline runs:
   - LLM generates the output (summary / answer)
   - Sentence-level attributions are computed
   - Top sentences are refined to phrase/word level
6. See the highlighted input document. Darker blue = higher importance.
7. Click any highlighted sentence to expand into finer-grained attributions.

## Configuration

Copy `.env.example` to `.env` and adjust. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `MEXGEN_DEVICE` | `auto` | `auto`, `cpu`, `cuda`, `mps` |
| `MEXGEN_SUMMARIZATION_MODEL` | `sshleifer/distilbart-xsum-12-6` | HF model ID |
| `MEXGEN_QA_MODEL` | `google/flan-t5-base` | HF model ID |
| `MEXGEN_SCALARIZER` | `prob` | `prob` (log-prob) or `text` (similarity) |
| `MEXGEN_ATTRIBUTION_METHOD` | `clime` | `clime`, `lshap`, `loo` |
| `MEXGEN_TOP_K_REFINE` | `3` | Number of top sentences to refine |

## API Reference

Once running, see OpenAPI docs at **http://localhost:8000/docs**.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check, model status |
| `/api/explain` | POST | Submit explanation job |
| `/api/jobs/{id}` | GET | Poll job result |
| `/api/jobs/{id}/status` | GET | Lightweight status |
| `/ws/jobs/{id}` | WS | Real-time progress stream |

## How It Works

MExGen explains context-grounded LLM outputs by:

1. **Segmenting** the input into linguistic units (sentences, phrases, words) using spaCy
2. **Perturbing** subsets of these units (dropping them from the input)
3. **Measuring** how much the output changes via scalarizers (log-prob, BERTScore, etc.)
4. **Fitting** a local linear model (C-LIME) or computing Shapley values (L-SHAP) to assign attribution scores
5. **Refining** the top-k most important sentences into finer units (phrases or words)

The result is a multi-level attribution map showing exactly which parts of the input context influenced the LLM's output.

## License

This application wraps the [ICX360 toolkit](https://github.com/IBM/ICX360) (Apache 2.0).
