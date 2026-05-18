# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

FastAPI microservice for **ReadRight Module 2** — the audio-based reading assessment pipeline. It transcribes a student reading a Phil-IRI passage aloud, classifies miscues, computes WPM + word recognition %, and returns a reading level. There is also a GO3 computer-vision pipeline (behavioral flags) that runs in parallel.

## Commands

```bash
# Activate venv (always required)
source .venv/bin/activate

# Run dev server (from project root, not from app/)
uvicorn app.main:app --reload

# Type check (strict — must be 0 errors before committing)
.venv/bin/pyright app/

# Install dependencies
pip install -r requirements.txt
# NOTE: ffmpeg system binary also required: sudo apt-get install ffmpeg
```

## Architecture

```
app/
  main.py              # App factory + lifespan (WhisperX preloads here)
  config.py            # pydantic-settings Settings, WHISPERX_MODEL/DEVICE configurable via .env
  dependencies.py      # FastAPI dependency providers (get_transcriber → TranscriberProtocol)
  routers/
    analyze.py         # AnalyzeController — HTTP only, no business logic
  services/
    go2/               # transcriber.py (done), miscue_classifier.py (RR-022), scoring_engine.py (RR-023)
    go3/               # CVDetector, ProsodyAmplitudeDetector (not this module's responsibility)
  models/
    assessment.py      # AssessmentResult Pydantic model — the single API response schema
    transcription.py   # WordSegment TypedDict + TranscriberProtocol
  utils/
    result_consolidator.py  # Merges GO2 + GO3 results (stub, wired in RR-020)
```

### Key Patterns

- **Class-based controllers** — no bare route functions. `AnalyzeController` registers routes via `router.add_api_route()`.
- **Protocol interfaces** — concrete classes satisfy Protocols (`TranscriberProtocol`). Concretes are only wired in `dependencies.py`.
- **Singleton at startup** — WhisperX models load once in the FastAPI `lifespan` context manager via `load_models()`. Never load per request.
- **Strong types** — Python 3.12, pyright strict. `type X = ...` aliases (PEP 695), `list[X]` not `List[X]`, `TypedDict` for data shapes. whisperx has no stubs — its calls use `# type: ignore[no-untyped-call]`, isolated to `transcriber.py`.

### Environment

`.env` (copy from `.env.example`):
```
API_KEY=your-secret-key
WHISPERX_MODEL=base          # use large-v3 on GPU VM
WHISPERX_DEVICE=cpu          # use cuda on GPU VM
```

`X-API-Key` header required on all `/analyze` calls.

## Task Status

| Issue | What | Status |
|---|---|---|
| RR-004 | Scaffold + stub `/analyze` | ✅ Done |
| RR-021 | WhisperX ASR + forced alignment | ✅ Done |
| RR-022 | Phil-IRI Miscue Classifier | ⬜ Next |
| RR-023 | WPM + Scoring + Reading Level | ⬜ |
| RR-020 | Real `/analyze` orchestrator | ⬜ Last |

## Domain Rules (non-negotiable per SRS)

**Phil-IRI Miscue Taxonomy** (RR-022):
- `correct` — edit distance ≤ 1
- `mispronunciation` — phonetically similar, edit distance 2–3
- `substitution` — completely different word
- `omission` — passage word absent from transcript
- `insertion` — extra transcript word not in passage
- `repetition` — same word consecutive in transcript
- `refusal_to_pronounce` — no clear transcription + score < 0.3
- On ambiguous classification: prefer conservative label (mispronunciation > substitution)

**WPM + Scoring Formulas** (RR-023):
```python
wpm = total_passage_words / (last_word_end - first_word_start) * 60

# Error miscues = mispronunciation + substitution + omission + refusal_to_pronounce
# NOT insertion or repetition
word_recognition_pct = (total_words - error_count) / total_words * 100

# Reading level — boundary ties go to the LOWER classification
if word_recognition_pct >= 97:   reading_level = "Independent"
elif word_recognition_pct >= 91: reading_level = "Instructional"
else:                             reading_level = "Frustration"
```

**RR-020 orchestrator**: `asyncio.gather(go2, go3)` in parallel, `try/finally` for temp file cleanup, Supabase service key (not learner JWT), 500 + error code on pipeline failure (`TRANSCRIPTION_FAILED`, `SCORING_FAILED`).

## Project Skills

`.claude/skills/` contains project-scoped workflow skills:
- `generate-and-verify` — the main coding loop: GENERATE → SHOW → APPROVE → WRITE → PYRIGHT → SOLID-CHECK → DOCSTRINGS → DESIGN-DOCS → JOURNAL
- `solid-oop` — SOLID + class-based OOP patterns for this project
- `python-strong-types` — pyright strict, Python 3.12 typing rules
- `design-docs` — HLD/LLD/UML generation under `docs/`
- `dev-journal` — append-only `docs/JOURNAL.md`

Always invoke `generate-and-verify` before writing any Python file.

## Docs

`docs/JOURNAL.md` — append-only iteration log. `docs/hld/`, `docs/lld/`, `docs/uml/` — Mermaid diagrams (VS Code Mermaid Viewer extension).
