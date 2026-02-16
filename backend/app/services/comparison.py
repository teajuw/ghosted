"""Before/after comparison logic - the centerpiece feature."""

from __future__ import annotations

from app.services.detectors.base import DetectionResult


def build_insight(
    chars_removed: int,
    changed_verdicts: list[dict],
    score_deltas: list[dict],
) -> tuple[str, str]:
    """Generate human-readable insight and reliability assessment.

    Returns (insight_text, reliability_assessment).
    """
    if chars_removed == 0:
        return (
            "No invisible characters were found, so original and cleaned results are identical.",
            "inconclusive",
        )

    changed_count = len(changed_verdicts)
    total_detectors = len(score_deltas)

    if total_detectors == 0:
        return "No detectors were available for comparison.", "inconclusive"

    # Calculate average absolute delta
    avg_delta = sum(abs(d["delta"]) for d in score_deltas) / total_detectors if total_detectors else 0

    parts = [f"Removed {chars_removed} invisible character{'s' if chars_removed != 1 else ''}."]

    if changed_count > 0:
        names = ", ".join(d["detector"] for d in changed_verdicts)
        parts.append(
            f"{changed_count} of {total_detectors} detector{'s' if total_detectors != 1 else ''} "
            f"changed verdict after cleaning ({names}). "
            f"This suggests {'these detectors rely' if changed_count > 1 else 'this detector relies'} "
            f"partly on invisible byte patterns rather than content analysis."
        )
        assessment = "byte_pattern_dependent"
    elif avg_delta > 0.05:
        parts.append(
            f"While no detectors changed their overall verdict, scores shifted by "
            f"{avg_delta:.0%} on average. Invisible characters had a measurable effect."
        )
        assessment = "byte_pattern_dependent"
    else:
        parts.append(
            "Detection scores remained stable after removing invisible characters. "
            "These detectors appear to analyze content rather than byte patterns."
        )
        assessment = "content_based"

    return " ".join(parts), assessment


def compare_results(
    original_results: list[DetectionResult],
    cleaned_results: list[DetectionResult],
) -> tuple[list[dict], list[dict]]:
    """Compare detection results before and after cleaning.

    Returns (changed_verdicts, score_deltas).
    """
    # Build lookup by detector name
    cleaned_by_name = {r.detector: r for r in cleaned_results if isinstance(r, DetectionResult)}

    changed_verdicts = []
    score_deltas = []

    for orig in original_results:
        if not isinstance(orig, DetectionResult):
            continue
        cleaned = cleaned_by_name.get(orig.detector)
        if cleaned is None:
            continue

        delta = cleaned.ai_score - orig.ai_score
        score_deltas.append({"detector": orig.detector, "delta": round(delta, 4)})

        if orig.verdict != cleaned.verdict:
            changed_verdicts.append({
                "detector": orig.detector,
                "before_verdict": orig.verdict,
                "after_verdict": cleaned.verdict,
                "before_ai_score": round(orig.ai_score, 4),
                "after_ai_score": round(cleaned.ai_score, 4),
                "score_delta": round(delta, 4),
            })

    return changed_verdicts, score_deltas
