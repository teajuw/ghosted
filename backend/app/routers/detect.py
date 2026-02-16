from fastapi import APIRouter

from app.models.schemas import (
    DetectRequest,
    DetectResponse,
    DetectorResult,
    DetectSummary,
    SentenceScore,
)
from app.services.detector_registry import get_registry
from app.services.detectors.base import DetectionResult

router = APIRouter()

DISCLAIMER = (
    "AI detection is probabilistic, not definitive. No detector is reliable enough "
    "to make accusations of academic dishonesty. These results show what automated "
    "tools see - they are not proof of anything. This tool is for educational and "
    "transparency purposes only."
)


def _result_to_response(r: DetectionResult) -> DetectorResult:
    sentence_scores = None
    if r.sentence_scores:
        sentence_scores = [
            SentenceScore(sentence=s.sentence, score=s.score)
            for s in r.sentence_scores
        ]
    return DetectorResult(
        detector=r.detector,
        detector_name=r.detector_name,
        verdict=r.verdict,
        ai_score=round(r.ai_score, 4),
        human_score=round(r.human_score, 4),
        method=r.method,
        note=r.note,
        sentence_scores=sentence_scores,
    )


def _build_summary(results: list[DetectionResult]) -> DetectSummary:
    if not results:
        return DetectSummary(
            consensus="uncertain",
            agreement_ratio=0.0,
            average_ai_score=0.0,
            disclaimer=DISCLAIMER,
        )

    verdicts = [r.verdict for r in results]
    ai_count = verdicts.count("likely_ai")
    human_count = verdicts.count("likely_human")
    total = len(verdicts)

    if ai_count == total:
        consensus = "likely_ai"
    elif human_count == total:
        consensus = "likely_human"
    elif ai_count > 0 and human_count > 0:
        consensus = "mixed"
    else:
        consensus = "uncertain"

    majority = max(ai_count, human_count, verdicts.count("uncertain"))
    agreement_ratio = majority / total if total else 0.0

    avg_ai = sum(r.ai_score for r in results) / total

    return DetectSummary(
        consensus=consensus,
        agreement_ratio=round(agreement_ratio, 4),
        average_ai_score=round(avg_ai, 4),
        disclaimer=DISCLAIMER,
    )


@router.post("/detect", response_model=DetectResponse)
async def detect(request: DetectRequest) -> DetectResponse:
    registry = get_registry()
    raw_results = await registry.detect_all(request.text, request.detectors)

    # Filter out exceptions
    successful = [r for r in raw_results if isinstance(r, DetectionResult)]

    results = [_result_to_response(r) for r in successful]
    summary = _build_summary(successful)

    return DetectResponse(results=results, summary=summary)
