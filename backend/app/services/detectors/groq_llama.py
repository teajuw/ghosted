"""Groq/Llama LLM-as-judge detectors using two different analysis strategies."""

from __future__ import annotations

import json

from groq import AsyncGroq

from app.services.detectors.base import BaseDetector, DetectionResult

STYLISTIC_SYSTEM_PROMPT = """\
You are a text analysis tool that detects stylistic markers of AI-generated content.

Analyze the text for these specific markers:
- Hedging phrases ("It's important to note", "It's worth mentioning")
- Excessive em-dash usage
- Overly balanced/diplomatic tone
- Generic transitions ("Furthermore", "Moreover", "Additionally")
- Lists that are too perfectly structured
- Lack of personal voice or specific details

Respond with ONLY valid JSON:
{"ai_probability": <float 0.0 to 1.0>, "markers_found": ["list"], "reasoning": "1-2 sentences"}"""

STRUCTURAL_SYSTEM_PROMPT = """\
You are a text analysis tool that detects structural patterns of AI-generated content.

Analyze the text for these patterns:
- Uniform paragraph lengths
- Consistent sentence length (low variance)
- Repetitive sentence structures
- Vocabulary that is unusually consistent in register
- Perfect grammar with no natural errors
- Formulaic introduction/conclusion patterns

Respond with ONLY valid JSON:
{"ai_probability": <float 0.0 to 1.0>, "patterns_found": ["list"], "reasoning": "1-2 sentences"}"""


class _GroqBaseDetector(BaseDetector):
    method = "llm_analysis"

    def __init__(self, api_key: str, system_prompt: str) -> None:
        self._api_key = api_key
        self._system_prompt = system_prompt

    def is_available(self) -> bool:
        return bool(self._api_key)

    async def detect(self, text: str) -> DetectionResult:
        client = AsyncGroq(api_key=self._api_key)
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": f"Analyze this text:\n\n{text[:3000]}"},
            ],
            temperature=0.1,
            max_tokens=500,
        )

        raw_text = response.choices[0].message.content or "{}"
        parsed = self._parse_response(raw_text)

        ai_score = parsed.get("ai_probability", 0.5)
        ai_score = max(0.0, min(1.0, ai_score))

        markers = parsed.get("markers_found") or parsed.get("patterns_found") or []
        reasoning = parsed.get("reasoning", "")
        note_parts = []
        if markers:
            note_parts.append(f"Markers: {', '.join(markers[:5])}")
        if reasoning:
            note_parts.append(reasoning)

        return DetectionResult(
            detector=self.name,
            detector_name=self.display_name,
            verdict=self._verdict_from_score(ai_score),
            ai_score=ai_score,
            human_score=1.0 - ai_score,
            method=self.method,
            note=". ".join(note_parts) if note_parts else "LLM-based analysis.",
        )

    def _parse_response(self, text: str) -> dict:
        """Extract JSON from the LLM response, handling markdown code blocks."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:])
            if text.endswith("```"):
                text = text[:-3]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return {}


class GroqStylisticDetector(_GroqBaseDetector):
    name = "groq_stylistic"
    display_name = "Llama Stylistic Analyzer"

    def __init__(self, api_key: str) -> None:
        super().__init__(api_key, STYLISTIC_SYSTEM_PROMPT)


class GroqStructuralDetector(_GroqBaseDetector):
    name = "groq_structural"
    display_name = "Llama Structural Analyzer"

    def __init__(self, api_key: str) -> None:
        super().__init__(api_key, STRUCTURAL_SYSTEM_PROMPT)
