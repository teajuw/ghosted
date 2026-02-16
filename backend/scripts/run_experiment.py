#!/usr/bin/env python3
"""Invisible Character Experiment for Ghosted.

Tests which invisible Unicode characters affect AI detection scores.

Design:
- 20 known-human text samples (varied categories)
- 8 character types injected individually
- 4 density levels: 1 char, 1%, 3%, 5% of text length
- Tested against RoBERTa via HuggingFace Inference API (free, unlimited-ish)
- Optionally validated against Sapling (use --sapling flag)

Usage:
    python3 scripts/run_experiment.py --hf-token hf_xxx [--sapling-key xxx]
    python3 scripts/run_experiment.py --hf-token hf_xxx --output data/experiment_results.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.fixtures.sample_texts import SAMPLES

HF_API_URL = "https://api-inference.huggingface.co/models"
SAPLING_API_URL = "https://api.sapling.ai/api/v1/aidetect"

# Characters to test
TEST_CHARS = {
    "U+200B": "\u200B",  # ZERO WIDTH SPACE
    "U+200C": "\u200C",  # ZERO WIDTH NON-JOINER
    "U+200D": "\u200D",  # ZERO WIDTH JOINER
    "U+FEFF": "\uFEFF",  # BOM
    "U+2060": "\u2060",  # WORD JOINER
    "U+201C/D": None,    # Smart quotes (special handling)
    "U+2014": "\u2014",  # EM DASH
    "MIX": None,         # Mix of all zero-width
}

DENSITIES = ["1_char", "1%", "3%", "5%"]

# RoBERTa models to test against
ROBERTA_MODELS = {
    "roberta_coai": "coai/roberta-ai-detector-v2",
    "roberta_openai": "openai-community/roberta-base-openai-detector",
}


def inject_chars(text: str, char_code: str, density: str) -> str:
    """Inject invisible characters into text at specified density."""
    if density == "1_char":
        # Single character at a random word boundary
        spaces = [i for i, c in enumerate(text) if c == " "]
        if spaces:
            pos = random.choice(spaces)
            char = _get_char(char_code)
            return text[:pos] + char + text[pos:]
        return text

    # Percentage-based density
    pct = float(density.rstrip("%")) / 100
    num_chars = max(1, int(len(text) * pct))

    if char_code == "U+201C/D":
        return _inject_smart_quotes(text, num_chars)

    char = _get_char(char_code)
    # Insert at random positions (between characters)
    positions = sorted(random.sample(range(len(text)), min(num_chars, len(text))), reverse=True)
    result = list(text)
    for pos in positions:
        result.insert(pos, char)
    return "".join(result)


def _get_char(char_code: str) -> str:
    if char_code == "MIX":
        return random.choice(["\u200B", "\u200C", "\u200D", "\uFEFF", "\u2060"])
    if char_code in TEST_CHARS and TEST_CHARS[char_code]:
        return TEST_CHARS[char_code]
    return "\u200B"  # fallback


def _inject_smart_quotes(text: str, count: int) -> str:
    """Replace ASCII quotes with smart quotes."""
    result = text
    replacements = 0
    for old, new in [('"', "\u201C"), ("'", "\u2018")]:
        while old in result and replacements < count:
            result = result.replace(old, new, 1)
            replacements += 1
    # If not enough quotes to replace, insert smart quotes at random positions
    while replacements < count:
        pos = random.randint(0, len(result))
        char = random.choice(["\u201C", "\u201D"])
        result = result[:pos] + char + result[pos:]
        replacements += 1
    return result


async def detect_hf(text: str, model_id: str, api_token: str) -> float:
    """Get AI score from HuggingFace Inference API. Returns ai_score 0-1."""
    url = f"{HF_API_URL}/{model_id}"
    headers = {"Authorization": f"Bearer {api_token}"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(3):
            resp = await client.post(url, headers=headers, json={"inputs": text[:512]})
            if resp.status_code == 503:
                # Model loading, wait and retry
                wait = resp.json().get("estimated_time", 20)
                print(f"  Model loading, waiting {wait:.0f}s...")
                await asyncio.sleep(min(wait, 60))
                continue
            if resp.status_code == 429:
                print("  Rate limited, waiting 10s...")
                await asyncio.sleep(10)
                continue
            resp.raise_for_status()
            data = resp.json()
            return _extract_ai_score(data)
    return -1.0  # Failed


async def detect_sapling(text: str, api_key: str) -> float:
    """Get AI score from Sapling API. Returns ai_score 0-1."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            SAPLING_API_URL,
            json={"key": api_key, "text": text},
        )
        if resp.status_code == 429:
            print("  Sapling rate limited")
            return -1.0
        resp.raise_for_status()
        return resp.json().get("score", -1.0)


def _extract_ai_score(data) -> float:
    results = data
    if isinstance(data, list) and data and isinstance(data[0], list):
        results = data[0]
    if not isinstance(results, list):
        return 0.5
    for item in results:
        label = item.get("label", "").upper()
        score = item.get("score", 0.0)
        if label in ("FAKE", "LABEL_1"):
            return score
        if label in ("REAL", "LABEL_0"):
            return 1.0 - score
    return 0.5


async def run_experiment(hf_token: str, sapling_key: str | None, output_path: str) -> None:
    print(f"Running experiment with {len(SAMPLES)} samples...")
    print(f"Characters: {len(TEST_CHARS)}, Densities: {len(DENSITIES)}")
    print(f"Total variants per model: {len(SAMPLES) * len(TEST_CHARS) * len(DENSITIES)}")
    print()

    results_by_char: dict[str, dict] = {}

    for char_code in TEST_CHARS:
        print(f"\n--- Testing {char_code} ---")
        char_results: dict[str, list] = {d: [] for d in DENSITIES}
        detector_results: dict[str, dict[str, list]] = {}

        for density in DENSITIES:
            for sample in SAMPLES:
                text = sample["text"]

                # Get baseline score (original text)
                baseline_scores: dict[str, float] = {}
                for det_name, model_id in ROBERTA_MODELS.items():
                    score = await detect_hf(text, model_id, hf_token)
                    if score >= 0:
                        baseline_scores[det_name] = score
                    await asyncio.sleep(0.5)  # Be nice to the API

                # Get injected score
                random.seed(42 + hash(sample["id"] + char_code + density))
                injected_text = inject_chars(text, char_code, density)

                injected_scores: dict[str, float] = {}
                for det_name, model_id in ROBERTA_MODELS.items():
                    score = await detect_hf(injected_text, model_id, hf_token)
                    if score >= 0:
                        injected_scores[det_name] = score
                    await asyncio.sleep(0.5)

                # Calculate deltas per detector
                for det_name in ROBERTA_MODELS:
                    if det_name in baseline_scores and det_name in injected_scores:
                        delta = injected_scores[det_name] - baseline_scores[det_name]
                        char_results[density].append(delta)

                        if det_name not in detector_results:
                            detector_results[det_name] = {d: [] for d in DENSITIES}
                        detector_results[det_name][density].append({
                            "sample": sample["id"],
                            "baseline": baseline_scores[det_name],
                            "injected": injected_scores[det_name],
                            "delta": delta,
                            "verdict_flipped": (
                                (baseline_scores[det_name] < 0.5) != (injected_scores[det_name] < 0.5)
                            ),
                        })

                print(f"  {density} | {sample['id'][:12]:12s} | done")

        # Aggregate results for this character
        by_density = {}
        for density in DENSITIES:
            deltas = char_results[density]
            by_density[density] = round(sum(deltas) / len(deltas), 4) if deltas else 0.0

        # Overall stats
        all_deltas = [d for density_deltas in char_results.values() for d in density_deltas]
        avg_delta = sum(abs(d) for d in all_deltas) / len(all_deltas) if all_deltas else 0.0

        # Verdict flip rate
        all_flips = []
        for det_data in detector_results.values():
            for density_data in det_data.values():
                for entry in density_data:
                    all_flips.append(entry["verdict_flipped"])
        flip_rate = sum(all_flips) / len(all_flips) if all_flips else 0.0

        # Assign threat level
        if avg_delta > 0.15 or flip_rate > 0.30:
            threat_level = "high"
        elif avg_delta > 0.05 or flip_rate > 0.10:
            threat_level = "medium"
        else:
            threat_level = "low"

        # Per-detector aggregation
        by_detector = {}
        for det_name, det_data in detector_results.items():
            det_all_deltas = [e["delta"] for d_data in det_data.values() for e in d_data]
            det_all_flips = [e["verdict_flipped"] for d_data in det_data.values() for e in d_data]
            by_detector[det_name] = {
                "avg_delta": round(sum(abs(d) for d in det_all_deltas) / len(det_all_deltas), 4) if det_all_deltas else 0.0,
                "flip_rate": round(sum(det_all_flips) / len(det_all_flips), 4) if det_all_flips else 0.0,
            }

        # Get char name
        char_names = {
            "U+200B": "ZERO WIDTH SPACE",
            "U+200C": "ZERO WIDTH NON-JOINER",
            "U+200D": "ZERO WIDTH JOINER",
            "U+FEFF": "ZERO WIDTH NO-BREAK SPACE / BOM",
            "U+2060": "WORD JOINER",
            "U+201C/D": "SMART QUOTES",
            "U+2014": "EM DASH",
            "MIX": "MIXED ZERO-WIDTH CHARACTERS",
        }

        results_by_char[char_code] = {
            "char_code": char_code,
            "char_name": char_names.get(char_code, "UNKNOWN"),
            "threat_level": threat_level,
            "avg_score_delta": round(avg_delta, 4),
            "verdict_flip_rate": round(flip_rate, 4),
            "by_density": by_density,
            "by_detector": by_detector,
        }

        print(f"  Result: threat={threat_level}, avg_delta={avg_delta:.4f}, flip_rate={flip_rate:.4f}")

    # Build final output
    output = {
        "methodology": {
            "corpus_size": len(SAMPLES),
            "char_types_tested": len(TEST_CHARS),
            "densities": DENSITIES,
            "detectors_used": list(ROBERTA_MODELS.keys()),
            "samples_per_variant": len(SAMPLES),
        },
        "results": list(results_by_char.values()),
        "threat_levels": {
            "high": {"min_delta": 0.15, "min_flip_rate": 0.30},
            "medium": {"min_delta": 0.05, "min_flip_rate": 0.10},
            "low": {"description": "Score delta < 5% and flip rate < 10%"},
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(output, indent=2))
    print(f"\nResults written to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Run the Ghosted invisible character experiment")
    parser.add_argument("--hf-token", required=True, help="HuggingFace API token")
    parser.add_argument("--sapling-key", help="Sapling API key (optional, for validation)")
    parser.add_argument("--output", default="data/experiment_results.json", help="Output file path")
    args = parser.parse_args()

    asyncio.run(run_experiment(args.hf_token, args.sapling_key, args.output))


if __name__ == "__main__":
    main()
