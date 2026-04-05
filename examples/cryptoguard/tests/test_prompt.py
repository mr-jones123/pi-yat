"""Tests for prompt construction."""

from __future__ import annotations

from cryptoguard.prompt import (
    SCAM_INDICATOR_PROMPTS,
    SYSTEM_PROMPT,
    build_analysis_prompt,
)


class TestPromptTemplates:
    def test_system_prompt_is_nonempty(self):
        assert len(SYSTEM_PROMPT) > 100

    def test_system_prompt_mentions_json(self):
        assert "JSON" in SYSTEM_PROMPT or "json" in SYSTEM_PROMPT

    def test_system_prompt_mentions_verdict(self):
        assert "verdict" in SYSTEM_PROMPT

    def test_scam_indicators_nonempty(self):
        assert len(SCAM_INDICATOR_PROMPTS) >= 5

    def test_scam_indicators_are_strings(self):
        for p in SCAM_INDICATOR_PROMPTS:
            assert isinstance(p, str)
            assert len(p) > 10


class TestBuildAnalysisPrompt:
    def test_includes_transcript(self):
        prompt = build_analysis_prompt(
            transcript="Send your Bitcoin to this address now!",
            clip_scores={"fake profit screenshot": 0.8},
        )
        assert "Send your Bitcoin" in prompt

    def test_includes_clip_scores(self):
        scores = {
            "fake profit screenshot": 0.85,
            "countdown timer": 0.3,
        }
        prompt = build_analysis_prompt(transcript="", clip_scores=scores)
        assert "0.850" in prompt
        assert "0.300" in prompt

    def test_empty_transcript_shows_no_speech(self):
        prompt = build_analysis_prompt(transcript="", clip_scores={})
        assert "no speech detected" in prompt

    def test_clip_scores_sorted_descending(self):
        scores = {"indicator_low": 0.1, "indicator_high": 0.9, "indicator_mid": 0.5}
        prompt = build_analysis_prompt(transcript="test", clip_scores=scores)
        high_pos = prompt.index("indicator_high")
        mid_pos = prompt.index("indicator_mid")
        low_pos = prompt.index("indicator_low")
        assert high_pos < mid_pos < low_pos

    def test_prompt_asks_for_json(self):
        prompt = build_analysis_prompt(transcript="x", clip_scores={})
        assert "JSON" in prompt or "json" in prompt.lower()
