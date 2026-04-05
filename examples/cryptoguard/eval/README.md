# CryptoGuard Evaluation

## Dataset Format

`dataset.json` contains labelled video samples:

```json
{
  "samples": [
    {
      "id": "unique_id",
      "url": "https://...",
      "ground_truth": "scam" | "legitimate",
      "notes": "optional annotation"
    }
  ]
}
```

## Building the Dataset

1. Collect short-form video URLs from platforms (YouTube Shorts, TikTok, etc.)
2. Label each as `scam` or `legitimate` based on manual review
3. Aim for balanced classes (≥25 each)
4. Add entries to `dataset.json`

### Scam indicators to look for during labelling
- Unrealistic profit claims ("guaranteed 10x returns")
- Urgency tactics ("only 5 spots left", countdown timers)
- Celebrity impersonation or fake endorsements
- Requests to send crypto to a wallet address
- Fake trading platform screenshots
- Too-good-to-be-true giveaway promises

### Legitimate crypto content examples
- News coverage of market movements
- Educational explainers about blockchain technology
- Legitimate project announcements from verified accounts
- Technical analysis with appropriate disclaimers

## Running Evaluation

```bash
python eval/evaluate.py --dataset eval/dataset.json --output eval/results.json
```

## Metrics

The evaluation computes:
- **Accuracy**: Overall correct predictions
- **Precision**: Of predicted scams, how many are actual scams
- **Recall**: Of actual scams, how many were detected
- **F1 Score**: Harmonic mean of precision and recall
- **FPR**: False positive rate (legitimate flagged as scam)
- **FNR**: False negative rate (scam missed as legitimate)

## Ablation Studies

Run with different configurations to compare:

```bash
# Image-only (no transcript)
VLM_MODE=api python eval/evaluate.py --dataset eval/dataset.json --output eval/results_visual_only.json

# Different grid sizes
N_FRAMES=4 GRID_COLS=2 python eval/evaluate.py --dataset eval/dataset.json --output eval/results_4frames.json
N_FRAMES=9 GRID_COLS=3 python eval/evaluate.py --dataset eval/dataset.json --output eval/results_9frames.json
```
