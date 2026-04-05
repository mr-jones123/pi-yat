"""Prompt templates and scam indicator definitions for CryptoGuard."""

# ---------------------------------------------------------------------------
# CLIP zero-shot scam indicator prompts
# ---------------------------------------------------------------------------

SCAM_INDICATOR_PROMPTS: list[str] = [
    "fake cryptocurrency profit screenshot showing unrealistic gains",
    "countdown timer creating urgency to invest immediately",
    "celebrity endorsement for cryptocurrency investment",
    "flashy money and luxury lifestyle montage",
    "QR code or wallet address for cryptocurrency deposit",
    "fake trading platform interface with guaranteed returns",
    "text overlay promising free cryptocurrency giveaway",
    "before and after wealth transformation testimonial",
    "professional looking but fabricated financial chart",
    "mobile phone screen showing fake bank account balance",
]

# ---------------------------------------------------------------------------
# Qwen3-VL system prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are CryptoGuard, an expert analyst specialising in detecting cryptocurrency \
scams in short-form videos. You receive:
1. An image grid composed of uniformly sampled frames from the video (read \
left-to-right, top-to-bottom as a temporal sequence).
2. A transcript of the audio from the video.
3. CLIP-based visual scam indicator scores (cosine similarity 0-1).

Your task is to determine whether the video is a cryptocurrency scam.

Respond ONLY with valid JSON in this exact schema:
{
  "verdict": "scam" | "legitimate" | "uncertain",
  "confidence": <float 0-1>,
  "reasoning": "<step-by-step chain-of-thought explanation>",
  "indicators": [
    {"name": "<indicator>", "score": <float 0-1>, "source": "vlm"}
  ]
}
"""

# ---------------------------------------------------------------------------
# User prompt builder
# ---------------------------------------------------------------------------

def build_analysis_prompt(
    transcript: str,
    clip_scores: dict[str, float],
) -> str:
    """Construct the user-side prompt including transcript and CLIP scores."""
    clip_section = "CLIP Visual Scam Indicator Scores:\n"
    for indicator, score in sorted(clip_scores.items(), key=lambda x: -x[1]):
        clip_section += f"  - {indicator}: {score:.3f}\n"

    transcript_section = "Audio Transcript:\n"
    if transcript.strip():
        transcript_section += f'  "{transcript.strip()}"\n'
    else:
        transcript_section += "  (no speech detected)\n"

    return (
        "Analyse the attached image grid (video frames in temporal order) "
        "together with the following evidence.\n\n"
        f"{clip_section}\n"
        f"{transcript_section}\n"
        "Step-by-step, determine whether this video is a crypto scam. "
        "Consider: unrealistic profit claims, urgency tactics, fake testimonials, "
        "impersonation of celebrities or platforms, suspicious wallet addresses, "
        "pump-and-dump language, and too-good-to-be-true promises.\n\n"
        "Respond with the JSON schema described in your instructions."
    )
