"""Base detector interface and result model."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SentenceScore:
    sentence: str
    score: float


@dataclass
class DetectionResult:
    detector: str
    detector_name: str
    verdict: str  # "likely_human" | "likely_ai" | "uncertain"
    ai_score: float  # 0.0 to 1.0
    human_score: float  # 0.0 to 1.0
    method: str  # "classifier" | "llm_analysis"
    note: str
    sentence_scores: list[SentenceScore] | None = None


class BaseDetector(ABC):
    name: str
    display_name: str
    method: str  # "classifier" | "llm_analysis"

    @abstractmethod
    async def detect(self, text: str) -> DetectionResult:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this detector can currently run (has API key, etc.)."""
        ...

    def _verdict_from_score(self, ai_score: float) -> str:
        if ai_score >= 0.7:
            return "likely_ai"
        elif ai_score <= 0.3:
            return "likely_human"
        return "uncertain"
