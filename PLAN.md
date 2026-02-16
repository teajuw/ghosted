# Ghosted

## Overview
"Don't let invisible characters decide your grade." - A tool that scans text for hidden Unicode artifacts, runs AI detection, and shows how invisible characters affect detection scores.

## Stack
- **Backend**: Python 3.11, FastAPI, Pydantic v2 (done)
- **Frontend**: React/Vite, Tailwind (pending)
- **APIs**: Sapling.ai, HuggingFace Inference, Groq/Llama
- **Deploy**: Render/Railway free tier

## Backend

### [x] Project scaffolding
### [x] Unicode scanner service (50+ char types, threat levels)
### [x] Scan + Clean API endpoints
### [x] Detector base class + registry (primary/fallback pattern)
### [x] 5 detectors: Sapling, COAI RoBERTa, OpenAI RoBERTa, Groq stylistic, Groq structural
### [x] Detect + Compare endpoints
### [x] Invisible character experiment script
### [x] Dockerfile

## Frontend

### [ ] Landing page
- Hero: "Don't let invisible characters cost you your grade"
- Subheadline about AI detectors flagging hidden Unicode
- Social proof stat from experiment (e.g., "A single character changed detection by X%")
- CTA: "Scan Your Text" -> Scanner page
- Secondary CTA: "See our research" -> Lab page
- Theme: clean/minimal academic (Notion/Linear style)

### [ ] Lab page (experiment results)
- Heatmap/table: which chars affect which detectors
- Key findings in plain language
- Methodology section
- Endpoint: `GET /api/v1/experiment-results`

### [ ] Scanner page - Stage 1 (scan)
- Paste text into document-style textarea
- "Scan" button
- Cascade animation: invisible chars highlight one by one as "found"
- Threat-level colors: red (high), yellow (medium), gray (low)
- Summary card: "Found X high-risk, Y medium-risk characters"
- "Clean & Copy" button + "Run Detection" button
- If clean: "No invisible characters detected" + option to run detection anyway

### [ ] Scanner page - Stage 2 (detect)
- Runs on user click from Stage 1
- Progress indicators per detector
- Transparent labels: "Primary" (Sapling) vs "Fallback" (RoBERTa)
- Dashboard cards: each detector's verdict + score
- If invisible chars were found: auto-shows before/after comparison
- Summary: consensus, agreement ratio

### [ ] Quota/status display
- Show Sapling usage: "42K / 50K chars remaining today"
- If exhausted: "Primary detector at daily limit. Using open-source detector."

## Contracts

### GET /api/v1/health
```json
Response: { "status": "ok", "version": "0.1.0" }
```

### POST /api/v1/scan
```json
Request:  { "text": "string", "include_smart_chars": false }
Response: {
  "has_invisible_chars": true,
  "total_invisible_count": 3,
  "char_count": 500,
  "categories": { "zero-width": 2, "bidi": 1 },
  "findings": [{ "char": "U+200B", "name": "ZERO WIDTH SPACE", "category": "zero-width", "threat_level": "high", "count": 2, "positions": [45, 123] }],
  "smart_chars": null,
  "context": { "explanation": "...", "likely_source": "tokenizer_artifact" }
}
```

### POST /api/v1/clean
```json
Request:  { "text": "string", "normalize_smart_chars": false }
Response: {
  "cleaned_text": "...",
  "original_length": 503,
  "cleaned_length": 500,
  "chars_removed": 3,
  "removals": [{ "char": "U+200B", "name": "ZERO WIDTH SPACE", "count": 2 }]
}
```

### POST /api/v1/detect
```json
Request:  { "text": "string", "detectors": null }
Response: {
  "results": [{
    "detector": "sapling",
    "detector_name": "Sapling AI Detector",
    "verdict": "likely_human",
    "ai_score": 0.15,
    "human_score": 0.85,
    "method": "classifier",
    "note": "Primary detector...",
    "sentence_scores": [{ "sentence": "...", "score": 0.1 }]
  }],
  "summary": {
    "consensus": "likely_human",
    "agreement_ratio": 0.8,
    "average_ai_score": 0.2,
    "disclaimer": "AI detection is probabilistic..."
  }
}
```

### POST /api/v1/compare
```json
Request:  { "text": "string", "detectors": null, "normalize_smart_chars": false }
Response: {
  "scan": { ... },
  "original_detection": { "results": [...], "summary": {...} },
  "cleaned_detection": { "results": [...], "summary": {...} },
  "comparison": {
    "chars_removed": 3,
    "detectors_that_changed_verdict": [{ "detector": "...", "before_verdict": "likely_ai", "after_verdict": "likely_human", "score_delta": -0.5 }],
    "score_deltas": [{ "detector": "sapling", "delta": -0.15 }],
    "insight": "Removed 3 invisible characters. 1 of 5 detectors changed verdict...",
    "reliability_assessment": "byte_pattern_dependent"
  },
  "disclaimer": "..."
}
```

### GET /api/v1/experiment-results
Returns experiment data (JSON). See plan file for full schema.

## Notes
- Backend runs at `http://localhost:8000`
- Need API keys in `.env` (see `.env.example`): Sapling, Groq, HuggingFace (all free)
- Experiment script needs to be run manually: `python3 scripts/run_experiment.py --hf-token xxx`
- Ethical line: remove invisible chars = fine, modify real content = out of scope
- All 51 backend tests passing
