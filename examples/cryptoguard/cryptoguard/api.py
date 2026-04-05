"""FastAPI application exposing the CryptoGuard analysis pipeline."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cryptoguard.config import Settings
from cryptoguard.models import AnalysisRequest, AnalysisResponse
from cryptoguard.pipeline import CryptoGuardPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(
    title="CryptoGuard API",
    description="VLM-based cryptocurrency scam detection in short-form videos",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = Settings()
pipeline = CryptoGuardPipeline(settings)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """Analyse a short-form video URL for crypto scam content."""
    if not request.url.strip():
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        result = await pipeline.analyze_url(request.url)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return result


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal error: {exc}"},
    )
