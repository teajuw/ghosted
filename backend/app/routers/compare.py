from fastapi import APIRouter

from app.models.schemas import (
    CompareRequest,
    CompareResponse,
    ScanResponse,
    CharFindingResponse,
    SmartCharFindingResponse,
    ScanContext,
    DetectResponse,
    DetectorResult,
    DetectSummary,
    SentenceScore,
    Comparison,
    VerdictChange,
    ScoreDelta,
)
from app.services.unicode_scanner import scan as scan_text, clean as clean_text
from app.services.detector_registry import get_registry
from app.services.detectors.base import DetectionResult
from app.services.comparison import compare_results, build_insight
from app.routers.detect import DISCLAIMER, _result_to_response, _build_summary

router = APIRouter()


def _scan_to_response(result) -> ScanResponse:
    findings = [
        CharFindingResponse(
            char=f.char, name=f.name, category=f.category,
            threat_level=f.threat_level, count=f.count, positions=f.positions,
        )
        for f in result.findings
    ]
    smart_chars = None
    if result.smart_chars is not None:
        smart_chars = [
            SmartCharFindingResponse(
                char=s.char, name=s.name, count=s.count, replacement=s.replacement,
            )
            for s in result.smart_chars
        ]
    return ScanResponse(
        has_invisible_chars=result.has_invisible_chars,
        total_invisible_count=result.total_invisible_count,
        char_count=result.char_count,
        categories=result.categories,
        findings=findings,
        smart_chars=smart_chars,
        context=ScanContext(**result.context),
    )


@router.post("/compare", response_model=CompareResponse)
async def compare(request: CompareRequest) -> CompareResponse:
    registry = get_registry()

    # Step 1: Scan for invisible chars
    scan_result = scan_text(request.text, include_smart_chars=request.normalize_smart_chars)

    # Step 2: Clean the text
    clean_result = clean_text(request.text, normalize_smart_chars=request.normalize_smart_chars)

    # Step 3: Detect on original and cleaned text concurrently
    import asyncio
    orig_task = registry.detect_all(request.text, request.detectors)
    clean_task = registry.detect_all(clean_result.cleaned_text, request.detectors)
    orig_raw, clean_raw = await asyncio.gather(orig_task, clean_task)

    # Filter to successful results
    orig_successful = [r for r in orig_raw if isinstance(r, DetectionResult)]
    clean_successful = [r for r in clean_raw if isinstance(r, DetectionResult)]

    # Step 4: Compare
    changed_verdicts, score_deltas = compare_results(orig_successful, clean_successful)
    insight, reliability = build_insight(
        clean_result.chars_removed, changed_verdicts, score_deltas
    )

    # Build response
    scan_response = _scan_to_response(scan_result)
    orig_detect = DetectResponse(
        results=[_result_to_response(r) for r in orig_successful],
        summary=_build_summary(orig_successful),
    )
    clean_detect = DetectResponse(
        results=[_result_to_response(r) for r in clean_successful],
        summary=_build_summary(clean_successful),
    )

    comparison = Comparison(
        chars_removed=clean_result.chars_removed,
        detectors_that_changed_verdict=[VerdictChange(**v) for v in changed_verdicts],
        score_deltas=[ScoreDelta(**d) for d in score_deltas],
        insight=insight,
        reliability_assessment=reliability,
    )

    return CompareResponse(
        scan=scan_response,
        original_detection=orig_detect,
        cleaned_detection=clean_detect,
        comparison=comparison,
        disclaimer=DISCLAIMER,
    )
