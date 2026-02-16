"""HuggingFace Inference API RoBERTa detectors."""

from __future__ import annotations

import httpx

from app.services.detectors.base import BaseDetector, DetectionResult

HF_API_URL = "https://api-inference.huggingface.co/models"


class HFRobertaDetector(BaseDetector):
    method = "classifier"

    def __init__(
        self,
        name: str,
        display_name: str,
        model_id: str,
        api_token: str,
    ) -> None:
        self.name = name
        self.display_name = display_name
        self._model_id = model_id
        self._api_token = api_token

    def is_available(self) -> bool:
        return bool(self._api_token)

    async def detect(self, text: str) -> DetectionResult:
        url = f"{HF_API_URL}/{self._model_id}"
        headers = {"Authorization": f"Bearer {self._api_token}"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                url,
                headers=headers,
                json={"inputs": text[:512]},  # RoBERTa max 512 tokens
            )
            resp.raise_for_status()
            data = resp.json()

        # HF returns [[{"label": "...", "score": ...}, ...]]
        # Normalize to our format
        ai_score = self._extract_ai_score(data)
        human_score = 1.0 - ai_score

        return DetectionResult(
            detector=self.name,
            detector_name=self.display_name,
            verdict=self._verdict_from_score(ai_score),
            ai_score=ai_score,
            human_score=human_score,
            method=self.method,
            note=f"Open-source classifier ({self._model_id}). Analyzes first 512 tokens.",
        )

    def _extract_ai_score(self, data: list | dict) -> float:
        """Extract AI probability from HuggingFace response.

        Different models use different label conventions:
        - openai-community: "Fake" (AI) / "Real" (human)
        - coai: "LABEL_1" (AI) / "LABEL_0" (human)
        """
        results = data
        if isinstance(data, list) and data and isinstance(data[0], list):
            results = data[0]

        if not isinstance(results, list):
            return 0.5

        for item in results:
            label = item.get("label", "").upper()
            score = item.get("score", 0.0)

            # OpenAI model labels
            if label == "FAKE":
                return score
            if label == "REAL":
                return 1.0 - score

            # COAI model labels
            if label == "LABEL_1":
                return score
            if label == "LABEL_0":
                return 1.0 - score

            # Generic: if label contains "AI" or "GENERATED"
            if "AI" in label or "GENERATED" in label or "FAKE" in label:
                return score

        # Fallback: return the score of the first label if unclear
        if results:
            return results[0].get("score", 0.5)
        return 0.5
