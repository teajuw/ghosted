from fastapi import APIRouter

from app.models.schemas import CleanRequest, CleanResponse, RemovalEntry
from app.services.unicode_scanner import clean as clean_text

router = APIRouter()


@router.post("/clean", response_model=CleanResponse)
async def clean(request: CleanRequest) -> CleanResponse:
    result = clean_text(request.text, normalize_smart_chars=request.normalize_smart_chars)

    removals = [
        RemovalEntry(char=r["char"], name=r["name"], count=r["count"])  # type: ignore[arg-type]
        for r in result.removals
    ]

    return CleanResponse(
        cleaned_text=result.cleaned_text,
        original_length=result.original_length,
        cleaned_length=result.cleaned_length,
        chars_removed=result.chars_removed,
        removals=removals,
    )
