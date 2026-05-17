# GO2 (ASR) Task Ordering — ReadRight Module 2

## Context

You're assigned to Module 2 / GO2 of the ReadRight project: the audio-based pipeline that transcribes a learner reading a Phil-IRI passage aloud, classifies miscues, and produces WPM + word-recognition % + reading-level. There are 5 issues in `issues.md` (RR-004, RR-020, RR-021, RR-022, RR-023). The issues file suggests day-slots, but several share the same slot and the dependencies between them aren't spelled out, so the order isn't obvious.

You're working **solo and sequential** (one task at a time, no parallelism), and the **frontend team is blocked** until they can POST to a working `/analyze` endpoint. Those two constraints fully determine the order.

## Recommended Order

Do them in this exact sequence. Each task strictly depends on the previous ones being done.

| # | Issue   | Why it goes here                                                                                            | Est.    |
| - | ------- | ----------------------------------------------------------------------------------------------------------- | ------- |
| 1 | RR-004  | Scaffold + stub `/analyze`. Zero deps, unblocks frontend immediately. Must be first.                        | 2–3 hrs |
| 2 | RR-021  | WhisperX ASR + forced alignment. HIGH RISK + EXTERNAL + longest (6–8 hrs). Do early so you have buffer.     | 6–8 hrs |
| 3 | RR-022  | Miscue classifier. Consumes RR-021's `[{word, start, end, score}]` output. Can't start without it.          | 4–5 hrs |
| 4 | RR-023  | WPM + scoring + reading level. Needs RR-022's count dict **and** RR-021's start/end timestamps.             | 2–3 hrs |
| 5 | RR-020  | Real orchestrator. Wires GO2 (and GO3) together and replaces the RR-004 stub. Must be last.                 | ~4 hrs  |

Total: ~18–23 hrs of focused work.

## Why this order (and not the order in `issues.md`)

The `issues.md` day-slots are roughly compatible with this order, but they assume a team where RR-022 and RR-023 can run in parallel with RR-021 on Day 2 AM. **You're solo**, so you have to pick one — and the right call is to front-load RR-021 because:

1. **RR-021 is the only HIGH RISK + EXTERNAL task.** WhisperX install, model download, and alignment library compatibility are the things most likely to derail you. Discover those problems on Day 1, not Day 2 evening.
2. **RR-022 and RR-023 are mechanical** — pure Python, deterministic, no external services. Once they have real transcript output to feed on, they go fast.
3. **The Phil-IRI rules are non-negotiable per SRS line 181.** RR-022 and RR-023 need to be implemented carefully and tested against the unit tests already specified in the issues (don't deviate from the formulas — the SRS calls deviation "invalidates the system").

## Critical-Path Dependencies (proof the order is forced)

```
RR-004 (scaffold)
   │
   ▼
RR-021 (WhisperX → [{word, start, end, score}])
   │
   ├─────────────────┐
   ▼                 │
RR-022 (counts dict) │
   │                 │
   └────────┬────────┘
            ▼
        RR-023 (wpm, word_rec_pct, reading_level)
            │
            ▼
        RR-020 (orchestrator — replaces stub from RR-004)
```

You cannot swap any pair without breaking a real data dependency.

## Per-Task Pointers

These are the things the SRS/SDD pinned down that the issue text doesn't fully repeat — flag them while implementing so you don't have to re-do work.

### RR-004 — Scaffold + Stub
- Set up the folder structure exactly as listed in the issue (`app/services/go2`, `app/services/go3`, etc.). RR-020 assumes this layout.
- The stub `/analyze` response must include **all 10 GO2 fields** of `AssessmentResultJSON` (SRS line 913: "no null or missing values"). Don't shortcut the stub schema or RR-022/RR-023 will quietly break frontend rendering later.
- CORS for `localhost:5173` per the issue.
- `GET /health` is required.

### RR-021 — WhisperX (do this with care, it's the long pole)
- **Load model ONCE at startup** via `app.on_event("startup")` — per-request loading will blow the 90-second SLA (SRS line 859).
- Output shape locked: `[{"word": str, "start": float, "end": float, "score": float}, ...]` — RR-022/023 depend on this exact shape.
- Use `whisperx.load_model("base", device="cpu", language="en")` per the issue. CPU is correct for the pilot.
- After your first real test run, document actual timing as a comment on the issue (per the DoD).
- Have a fallback plan in case WhisperX install breaks: be ready to flag it to the team early.

### RR-022 — Miscue Classifier
- **Phil-IRI taxonomy is non-negotiable** (SRS line 181). The 7 categories and their definitions in the issue are authoritative.
- Implement the 4 unit tests in the issue *as you build*, not after. They double as the spec.
- Handle: empty transcript (all omissions), extra trailing words (insertions), perfect read (all correct).
- On ambiguous classification, prefer the more conservative label (SRS line 559: Mispronunciation > Substitution).

### RR-023 — WPM + Scoring + Reading Level
- **Three exact reading-level strings only:** `"Frustration"`, `"Instructional"`, `"Independent"`. Anything else breaks the frontend.
- **Error miscues** for word-recognition % = mispronunciation + substitution + omission + refusal_to_pronounce. **NOT** insertion or repetition (Phil-IRI rule, restated in SRS lines 594–595).
- **Boundary rule:** On exact-threshold ties, apply the *lower* classification (SRS line 633).
- Run all 4 unit tests from the issue — they're the acceptance criteria.

### RR-020 — Real Orchestrator
- Replace the stub from RR-004; don't leave a duplicate handler.
- `asyncio.gather(run_go2_pipeline, run_go3_pipeline)` runs both pipelines in parallel — this is part of how you hit the 90-second SLA.
- `try/finally` for temp file cleanup is mandatory (DoD requires filesystem verification).
- Use the **Supabase service key**, not a learner JWT (SDD architecture: service writes session results).
- On either pipeline failure → 500 with error code (`TRANSCRIPTION_FAILED` per SRS line 523, `SCORING_FAILED` per SRS line 599).

## Critical Files (once they exist)

- `app/main.py` — FastAPI app, CORS, **startup hook for WhisperX model load**
- `app/routers/analyze.py` — stub in RR-004, real orchestrator in RR-020
- `app/services/go2/transcriber.py` — RR-021
- `app/services/go2/miscue_classifier.py` — RR-022
- `app/services/go2/scoring_engine.py` — RR-023
- `app/models/assessment.py` — `AssessmentResultJSON` Pydantic model (set up in RR-004, consumed by all downstream)
- `app/utils/result_consolidator.py` — used by RR-020 to merge GO2 + GO3
- `requirements.txt` — pinned in RR-004

## Verification (end of each task)

- **RR-004:** `uvicorn app.main:app --reload` boots; `curl -X POST -F file=@any.mp4 -F passage_id=p1 -H "X-API-Key: ..." localhost:8000/analyze` returns 200 with the full stub JSON; wrong key → 401.
- **RR-021:** Feed a real 2-minute WAV → get a word list with timestamps in <90s on CPU. Model loads at startup, not per request (check the logs).
- **RR-022:** All 4 unit tests in the issue pass. Manually feed a known transcript+passage pair and check counts.
- **RR-023:** All 4 unit tests in the issue pass (66.7 WPM, 94% → Instructional, 86% → Frustration, 100% → Independent). Confirm output keys match `AssessmentResultJSON` GO2 fields exactly.
- **RR-020:** Record a real reading on Chrome Android (webm) AND iOS Safari (mp4), POST to `/analyze`, verify: full JSON returned, Supabase row written, temp files gone (`ls /tmp/*.wav` → none). Force a pipeline failure → 500 with error code.
