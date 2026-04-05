FROM python:3.12-slim AS base

WORKDIR /app

# System deps for spacy and torch
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy and install Python deps
COPY pyproject.toml .
RUN uv pip install --system . && \
    python -m spacy download en_core_web_sm

# Copy app code
COPY app/ app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
