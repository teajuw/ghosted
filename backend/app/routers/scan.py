from fastapi import APIRouter

from app.models.schemas import (
    ScanRequest,
    ScanResponse,
    CharFindingResponse,
    SmartCharFindingResponse,
    ScanContext,
)
from app.services.unicode_scanner import scan as scan_text

router = APIRouter()


@router.post("/scan", response_model=ScanResponse)
async def scan(request: ScanRequest) -> ScanResponse:
    result = scan_text(request.text, include_smart_chars=request.include_smart_chars)

    findings = [
        CharFindingResponse(
            char=f.char,
            name=f.name,
            category=f.category,
            threat_level=f.threat_level,
            count=f.count,
            positions=f.positions,
        )
        for f in result.findings
    ]

    smart_chars = None
    if result.smart_chars is not None:
        smart_chars = [
            SmartCharFindingResponse(
                char=s.char, name=s.name, count=s.count, replacement=s.replacement
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
