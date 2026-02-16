"""Pydantic request/response models for all API endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


# --- Scan ---

class ScanRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50_000)
    include_smart_chars: bool = False


class CharFindingResponse(BaseModel):
    char: str
    name: str
    category: str
    threat_level: str
    count: int
    positions: list[int]


class SmartCharFindingResponse(BaseModel):
    char: str
    name: str
    count: int
    replacement: str


class ScanContext(BaseModel):
    explanation: str
    likely_source: str


class ScanResponse(BaseModel):
    has_invisible_chars: bool
    total_invisible_count: int
    char_count: int
    categories: dict[str, int]
    findings: list[CharFindingResponse]
    smart_chars: list[SmartCharFindingResponse] | None = None
    context: ScanContext


# --- Clean ---

class CleanRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50_000)
    normalize_smart_chars: bool = False


class RemovalEntry(BaseModel):
    char: str
    name: str
    count: int


class CleanResponse(BaseModel):
    cleaned_text: str
    original_length: int
    cleaned_length: int
    chars_removed: int
    removals: list[RemovalEntry]


# --- Detect ---

class DetectRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000)
    detectors: list[str] | None = None


class SentenceScore(BaseModel):
    sentence: str
    score: float


class DetectorResult(BaseModel):
    detector: str
    detector_name: str
    verdict: str  # "likely_human" | "likely_ai" | "uncertain"
    ai_score: float
    human_score: float
    method: str  # "classifier" | "llm_analysis"
    note: str
    sentence_scores: list[SentenceScore] | None = None


class DetectSummary(BaseModel):
    consensus: str  # "likely_human" | "likely_ai" | "mixed" | "uncertain"
    agreement_ratio: float
    average_ai_score: float
    disclaimer: str


class DetectResponse(BaseModel):
    results: list[DetectorResult]
    summary: DetectSummary


# --- Compare ---

class CompareRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000)
    detectors: list[str] | None = None
    normalize_smart_chars: bool = False


class VerdictChange(BaseModel):
    detector: str
    before_verdict: str
    after_verdict: str
    before_ai_score: float
    after_ai_score: float
    score_delta: float


class ScoreDelta(BaseModel):
    detector: str
    delta: float


class Comparison(BaseModel):
    chars_removed: int
    detectors_that_changed_verdict: list[VerdictChange]
    score_deltas: list[ScoreDelta]
    insight: str
    reliability_assessment: str  # "byte_pattern_dependent" | "content_based" | "inconclusive"


class CompareResponse(BaseModel):
    scan: ScanResponse
    original_detection: DetectResponse
    cleaned_detection: DetectResponse
    comparison: Comparison
    disclaimer: str
