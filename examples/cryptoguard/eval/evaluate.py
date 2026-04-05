#!/usr/bin/env python3
"""Evaluation script: run the pipeline on a labelled dataset and compute metrics.

Usage:
    python eval/evaluate.py --dataset eval/dataset.json [--output eval/results.json]
"""

from __future__ import annotations

import argparse
import asyncio
import json
from collections import Counter


def compute_metrics(
    predictions: list[str], ground_truths: list[str]
) -> dict[str, float]:
    """Compute accuracy, precision, recall, F1, FPR, FNR for binary scam detection.

    Treats 'scam' as the positive class.  'uncertain' predictions are counted
    as false negatives (missed scams) when ground truth is 'scam', and false
    positives otherwise.
    """
    tp = fp = tn = fn = 0

    for pred, gt in zip(predictions, ground_truths):
        pred_pos = pred == "scam"
        gt_pos = gt == "scam"

        if pred == "uncertain":
            # Conservative: uncertain on actual scam = missed
            if gt_pos:
                fn += 1
            else:
                tn += 1
            continue

        if gt_pos and pred_pos:
            tp += 1
        elif gt_pos and not pred_pos:
            fn += 1
        elif not gt_pos and pred_pos:
            fp += 1
        else:
            tn += 1

    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    fpr = fp / (fp + tn) if (fp + tn) else 0
    fnr = fn / (fn + tp) if (fn + tp) else 0

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "fpr": round(fpr, 4),
        "fnr": round(fnr, 4),
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "total": total,
    }


async def run_evaluation(dataset_path: str, output_path: str | None = None):
    from cryptoguard.pipeline import CryptoGuardPipeline

    with open(dataset_path) as f:
        dataset = json.load(f)

    samples = dataset["samples"]
    print(f"Evaluating {len(samples)} samples ...\n")

    pipe = CryptoGuardPipeline()
    predictions = []
    ground_truths = []
    details = []

    for i, sample in enumerate(samples):
        sid = sample["id"]
        url = sample["url"]
        gt = sample["ground_truth"]
        print(f"[{i + 1}/{len(samples)}] {sid}: {url}")

        resp = await pipe.analyze_url(url)
        pred = resp.result.verdict.value

        predictions.append(pred)
        ground_truths.append(gt)

        correct = "✓" if pred == gt else "✗"
        print(f"  {correct} predicted={pred} (gt={gt}, conf={resp.result.confidence:.2f})")

        details.append({
            "id": sid,
            "url": url,
            "ground_truth": gt,
            "prediction": pred,
            "confidence": resp.result.confidence,
            "reasoning": resp.result.reasoning[:200],
            "correct": pred == gt,
        })

    metrics = compute_metrics(predictions, ground_truths)

    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    for k, v in metrics.items():
        print(f"  {k:>12}: {v}")

    print(f"\nPrediction distribution: {dict(Counter(predictions))}")
    print(f"Ground truth distribution: {dict(Counter(ground_truths))}")

    result = {
        "dataset": dataset_path,
        "n_samples": len(samples),
        "metrics": metrics,
        "details": details,
    }

    if output_path:
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nResults saved to {output_path}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Evaluate CryptoGuard pipeline")
    parser.add_argument("--dataset", required=True, help="Path to dataset JSON")
    parser.add_argument("--output", default=None, help="Path to save results JSON")
    args = parser.parse_args()

    asyncio.run(run_evaluation(args.dataset, args.output))


if __name__ == "__main__":
    main()
