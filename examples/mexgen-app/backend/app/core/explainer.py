"""Core explanation engine wrapping icx360 MExGen.

Translates API requests into icx360 calls and normalises the output
into the UnitAttribution schema expected by the frontend.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from icx360.algorithms.mexgen.clime import CLIME
from icx360.algorithms.mexgen.lshap import LSHAP

from app.config import settings
from app.schemas.types import (
    AttributionMethod,
    TaskType,
    UnitAttribution,
)

if TYPE_CHECKING:
    from icx360.utils.model_wrappers import HFModel

logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _build_explainer(model: HFModel, method: AttributionMethod, scalarizer: str) -> CLIME | LSHAP:
    """Instantiate the right MExGen explainer variant."""
    kwargs: dict = {}
    if scalarizer == "text":
        kwargs["sim_scores"] = settings.text_scalarizers

    cls = CLIME if method == AttributionMethod.clime else LSHAP
    return cls(model=model, segmenter=settings.spacy_model, scalarizer=scalarizer, **kwargs)


def _format_prompt(document: str, task: TaskType, question: str | None = None) -> str:
    """Build the prompt string that gets sent to the model."""
    if task == TaskType.summarization:
        return document
    if task == TaskType.question_answering:
        if not question:
            raise ValueError("Question is required for QA task")
        return f"Context: {document}\n\nQuestion: {question}"
    raise ValueError(f"Unknown task: {task}")


def _normalise_scores(scores: np.ndarray) -> np.ndarray:
    """Min-max normalise scores to [-1, 1]."""
    lo, hi = scores.min(), scores.max()
    if hi == lo:
        return np.zeros_like(scores)
    return 2 * (scores - lo) / (hi - lo) - 1


def _pick_score_key(attributions: dict) -> str:
    """Find the attribution-score key in the output dict (varies by scalarizer)."""
    skip = {"units", "unit_types"}
    for key in attributions:
        if key not in skip:
            return key
    raise KeyError("No score key found in attributions dict")


# ── Public API ───────────────────────────────────────────────────────────────


def generate_output(model: HFModel, prompt: str, task: TaskType) -> str:
    """Run the LLM to get the baseline output text."""
    outputs = model.generate([prompt], text_only=True)
    return outputs[0] if isinstance(outputs, list) else outputs


def explain_coarse(
    model: HFModel,
    document: str,
    generated_output: str,
    task: TaskType,
    question: str | None,
    method: AttributionMethod,
    scalarizer: str,
    on_progress: callable | None = None,
) -> list[UnitAttribution]:
    """Compute sentence-level attributions (coarse pass)."""
    explainer = _build_explainer(model, method, scalarizer)

    prompt = _format_prompt(document, task, question)

    logger.info("Running coarse explanation (%s, %s scalarizer)", method.value, scalarizer)
    if on_progress:
        on_progress(0.1)

    explain_kwargs: dict = dict(
        input_orig=prompt,
        unit_types="p",
        output_orig=generated_output,
        ind_segment=True,
        segment_type="s",
        model_params={},
        scalarize_params={},
    )
    if method == AttributionMethod.clime:
        explain_kwargs["oversampling_factor"] = settings.oversampling_factor
        explain_kwargs["max_units_replace"] = settings.max_units_replace

    result = explainer.explain_instance(**explain_kwargs)
    if on_progress:
        on_progress(0.6)

    attrs = result["attributions"]
    units = attrs["units"]
    unit_types = attrs["unit_types"]
    score_key = _pick_score_key(attrs)
    raw_scores = np.asarray(attrs[score_key], dtype=float)
    normed = _normalise_scores(raw_scores)

    attributions = []
    for i, (text, utype, score) in enumerate(zip(units, unit_types, normed)):
        attributions.append(UnitAttribution(text=text, unit_type=utype, score=float(score), index=i))

    if on_progress:
        on_progress(0.7)

    return attributions


def explain_fine(
    model: HFModel,
    document: str,
    generated_output: str,
    task: TaskType,
    question: str | None,
    method: AttributionMethod,
    scalarizer: str,
    coarse_attributions: list[UnitAttribution],
    on_progress: callable | None = None,
) -> list[UnitAttribution]:
    """Refine the top-k coarse units into phrase/word-level attributions (fine pass).

    Returns a new attribution list where refined units contain children.
    """
    explainer = _build_explainer(model, method, scalarizer)
    prompt = _format_prompt(document, task, question)

    # Identify units to refine: top-k by score that exceed threshold
    scoreable = [a for a in coarse_attributions if a.unit_type != "n"]
    scoreable.sort(key=lambda a: a.score, reverse=True)
    threshold = settings.refine_threshold
    to_refine_indices = set()
    for a in scoreable[: settings.top_k_refine]:
        if a.score >= threshold:
            to_refine_indices.add(a.index)

    if not to_refine_indices:
        logger.info("No units above threshold for refinement")
        if on_progress:
            on_progress(1.0)
        return coarse_attributions

    # Build mixed-level input: refined units get segmented into phrases/words,
    # others stay as-is
    coarse_units = [a.text for a in coarse_attributions]
    coarse_types = [a.unit_type for a in coarse_attributions]

    ind_segment = [i in to_refine_indices for i in range(len(coarse_attributions))]
    fine_segment_type = "ph" if task == TaskType.summarization else "w"

    logger.info("Refining %d units at %s level", len(to_refine_indices), fine_segment_type)
    if on_progress:
        on_progress(0.75)

    explain_kwargs: dict = dict(
        input_orig=coarse_units,
        unit_types=coarse_types,
        output_orig=generated_output,
        ind_segment=ind_segment,
        segment_type=fine_segment_type,
        model_params={},
        scalarize_params={},
    )
    if method == AttributionMethod.clime:
        explain_kwargs["oversampling_factor"] = settings.oversampling_factor
        explain_kwargs["max_units_replace"] = settings.max_units_replace

    result = explainer.explain_instance(**explain_kwargs)
    if on_progress:
        on_progress(0.95)

    attrs = result["attributions"]
    fine_units = attrs["units"]
    fine_types = attrs["unit_types"]
    score_key = _pick_score_key(attrs)
    raw_scores = np.asarray(attrs[score_key], dtype=float)
    normed = _normalise_scores(raw_scores)

    # Re-group fine units back under their coarse parents
    fine_flat = [
        UnitAttribution(text=t, unit_type=ut, score=float(s), index=j)
        for j, (t, ut, s) in enumerate(zip(fine_units, fine_types, normed))
    ]

    # Build output: for non-refined units, keep as-is.
    # For refined units, assign children from the fine pass.
    output: list[UnitAttribution] = []
    fine_idx = 0
    for coarse_attr in coarse_attributions:
        if coarse_attr.index in to_refine_indices:
            # Collect fine children that came from this coarse unit
            children: list[UnitAttribution] = []
            coarse_text = coarse_attr.text
            consumed = ""
            while fine_idx < len(fine_flat):
                child = fine_flat[fine_idx]
                children.append(child)
                consumed += child.text
                fine_idx += 1
                # Stop when we've consumed roughly the full coarse unit
                if len(consumed.strip()) >= len(coarse_text.strip()):
                    break
            # Parent score = max of children
            parent_score = max((c.score for c in children), default=coarse_attr.score)
            output.append(
                UnitAttribution(
                    text=coarse_attr.text,
                    unit_type=coarse_attr.unit_type,
                    score=parent_score,
                    index=coarse_attr.index,
                    children=children,
                )
            )
        else:
            output.append(coarse_attr)
            fine_idx += 1  # this unit appears as-is in the fine list

    if on_progress:
        on_progress(1.0)

    return output
