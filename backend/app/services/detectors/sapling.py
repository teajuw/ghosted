"""Sapling.ai AI detector - primary detector with sentence-level scoring."""

from __future__ import annotations

import httpx

from app.services.detectors.base import BaseDetector, DetectionResult, SentenceScore

SAPLING_API_URL = "https://api.sapling.ai/api/v1/aidetect"


class SaplingDetector(BaseDetector):
    name = "sapling"
    display_name = "Sapling AI Detector"
    method = "classifier"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def is_available(self) -> bool:
        return bool(self._api_key)

    async def detect(self, text: str) -> DetectionResult:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                SAPLING_API_URL,
                json={
                    "key": self._api_key,
                    "text": text,
                    "sent_scores": True,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        ai_score = data.get("score", 0.0)
        human_score = 1.0 - ai_score

        # Parse sentence-level scores
        sentence_scores = None
        raw_sent_scores = data.get("sentence_scores")
        if raw_sent_scores:
            sentence_scores = [
                SentenceScore(sentence=item.get("sentence", ""), score=item.get("score", 0.0))
                for item in raw_sent_scores
                if isinstance(item, dict)
            ]

        return DetectionResult(
            detector=self.name,
            detector_name=self.display_name,
            verdict=self._verdict_from_score(ai_score),
            ai_score=ai_score,
            human_score=human_score,
            method=self.method,
            note="Primary detector. Trained on GPT-5, Claude 4.5, Gemini 2.5, DeepSeek-V3.",
            sentence_scores=sentence_scores,
        )
