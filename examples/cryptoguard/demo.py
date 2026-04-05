#!/usr/bin/env python3
"""CLI demo: analyse a single video URL and print the verdict."""

from __future__ import annotations

import asyncio
import json
import sys


async def main(url: str) -> None:
    from cryptoguard.pipeline import CryptoGuardPipeline

    print(f"🔍 Analysing: {url}\n")
    pipe = CryptoGuardPipeline()
    resp = await pipe.analyze_url(url)

    r = resp.result
    verdict_emoji = {"scam": "🚨", "legitimate": "✅", "uncertain": "❓"}
    print(f"{verdict_emoji.get(r.verdict.value, '❓')} Verdict: {r.verdict.value.upper()}")
    print(f"   Confidence: {r.confidence:.0%}")
    print(f"   Duration: {resp.duration_seconds:.1f}s\n")

    print("📝 Reasoning:")
    print(f"   {r.reasoning}\n")

    if r.indicators:
        print("🔎 VLM-detected indicators:")
        for ind in r.indicators:
            print(f"   [{ind.source}] {ind.name}: {ind.score:.2f}")
        print()

    if r.clip_scores:
        print("📊 CLIP visual scam scores:")
        for name, score in sorted(r.clip_scores.items(), key=lambda x: -x[1]):
            bar = "█" * int(score * 20)
            print(f"   {score:.3f} {bar} {name}")
        print()

    if r.transcript:
        print("🎤 Transcript:")
        print(f'   "{r.transcript[:500]}"')

    # Also dump full JSON for programmatic use
    print("\n--- Full JSON ---")
    print(json.dumps(resp.model_dump(exclude={"image_grid_b64"}), indent=2, default=str))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python demo.py <video-url>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
