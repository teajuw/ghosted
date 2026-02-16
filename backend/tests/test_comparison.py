"""Tests for comparison logic."""

from app.services.comparison import compare_results, build_insight
from app.services.detectors.base import DetectionResult


def _make_result(detector: str, ai_score: float, verdict: str) -> DetectionResult:
    return DetectionResult(
        detector=detector,
        detector_name=detector,
        verdict=verdict,
        ai_score=ai_score,
        human_score=1.0 - ai_score,
        method="classifier",
        note="test",
    )


class TestCompareResults:
    def test_no_change(self):
        orig = [_make_result("d1", 0.8, "likely_ai")]
        cleaned = [_make_result("d1", 0.8, "likely_ai")]
        changed, deltas = compare_results(orig, cleaned)
        assert len(changed) == 0
        assert len(deltas) == 1
        assert deltas[0]["delta"] == 0.0

    def test_verdict_changed(self):
        orig = [_make_result("d1", 0.8, "likely_ai")]
        cleaned = [_make_result("d1", 0.3, "likely_human")]
        changed, deltas = compare_results(orig, cleaned)
        assert len(changed) == 1
        assert changed[0]["before_verdict"] == "likely_ai"
        assert changed[0]["after_verdict"] == "likely_human"
        assert changed[0]["score_delta"] == -0.5

    def test_multiple_detectors(self):
        orig = [
            _make_result("d1", 0.8, "likely_ai"),
            _make_result("d2", 0.5, "uncertain"),
        ]
        cleaned = [
            _make_result("d1", 0.3, "likely_human"),
            _make_result("d2", 0.5, "uncertain"),
        ]
        changed, deltas = compare_results(orig, cleaned)
        assert len(changed) == 1  # Only d1 changed
        assert len(deltas) == 2

    def test_missing_detector_in_cleaned(self):
        orig = [_make_result("d1", 0.8, "likely_ai")]
        cleaned = []  # d1 failed on cleaned text
        changed, deltas = compare_results(orig, cleaned)
        assert len(changed) == 0
        assert len(deltas) == 0


class TestBuildInsight:
    def test_no_chars_removed(self):
        insight, assessment = build_insight(0, [], [])
        assert "identical" in insight.lower()
        assert assessment == "inconclusive"

    def test_verdict_changed(self):
        changed = [{"detector": "d1"}]
        deltas = [{"detector": "d1", "delta": -0.5}]
        insight, assessment = build_insight(3, changed, deltas)
        assert "byte pattern" in insight.lower()
        assert assessment == "byte_pattern_dependent"

    def test_score_shifted_no_verdict_change(self):
        changed = []
        deltas = [{"detector": "d1", "delta": 0.1}]
        insight, assessment = build_insight(5, changed, deltas)
        assert "shifted" in insight.lower() or "measurable" in insight.lower()
        assert assessment == "byte_pattern_dependent"

    def test_stable_scores(self):
        changed = []
        deltas = [{"detector": "d1", "delta": 0.01}]
        insight, assessment = build_insight(2, changed, deltas)
        assert "stable" in insight.lower() or "content" in insight.lower()
        assert assessment == "content_based"
