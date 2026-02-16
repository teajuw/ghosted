"""Registry for managing AI detectors with primary/fallback logic."""

from __future__ import annotations

import asyncio
import logging

from app.services.detectors.base import BaseDetector, DetectionResult

logger = logging.getLogger(__name__)


class DetectorRegistry:
    def __init__(self) -> None:
        self._detectors: dict[str, BaseDetector] = {}

    def register(self, detector: BaseDetector) -> None:
        self._detectors[detector.name] = detector

    def get(self, name: str) -> BaseDetector | None:
        return self._detectors.get(name)

    def get_available(self) -> list[str]:
        return [name for name, d in self._detectors.items() if d.is_available()]

    def get_all_names(self) -> list[str]:
        return list(self._detectors.keys())

    async def detect_all(
        self, text: str, detector_names: list[str] | None = None
    ) -> list[DetectionResult | Exception]:
        """Run detection across multiple detectors concurrently.

        Returns a list of results or exceptions (for failed detectors).
        """
        targets = detector_names or self.get_available()
        detectors = [self._detectors[n] for n in targets if n in self._detectors]

        if not detectors:
            return []

        tasks = [d.detect(text) for d in detectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any failures
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(
                    "Detector %s failed: %s", detectors[i].name, str(result)
                )

        return results  # type: ignore[return-value]


# Singleton registry - initialized lazily
_registry: DetectorRegistry | None = None


def get_registry() -> DetectorRegistry:
    global _registry
    if _registry is None:
        _registry = _init_registry()
    return _registry


def _init_registry() -> DetectorRegistry:
    from app.config import settings
    from app.services.detectors.sapling import SaplingDetector
    from app.services.detectors.hf_roberta import HFRobertaDetector
    from app.services.detectors.groq_llama import GroqStylisticDetector, GroqStructuralDetector

    registry = DetectorRegistry()

    # Tier 1: Primary
    registry.register(SaplingDetector(api_key=settings.sapling_api_key))
    registry.register(
        HFRobertaDetector(
            name="hf_roberta_coai",
            display_name="COAI Academic AI Detector v2",
            model_id="coai/roberta-ai-detector-v2",
            api_token=settings.hf_api_token,
        )
    )

    # Tier 2: Supplementary
    registry.register(
        HFRobertaDetector(
            name="hf_roberta_openai",
            display_name="OpenAI RoBERTa Detector (Baseline)",
            model_id="openai-community/roberta-base-openai-detector",
            api_token=settings.hf_api_token,
        )
    )
    registry.register(GroqStylisticDetector(api_key=settings.groq_api_key))
    registry.register(GroqStructuralDetector(api_key=settings.groq_api_key))

    return registry
