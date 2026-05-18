# Dev Journal — ReadRight GO2

> Append-only log of each build iteration. Newest entries at the bottom.

---

### 2026-05-17 · Iteration 1 — RR-004 GO2 Scaffold + Stub `/analyze`

**Added**
- `app/__init__.py`, `app/models/__init__.py`, `app/routers/__init__.py`, `app/services/__init__.py`, `app/services/go2/__init__.py`, `app/services/go3/__init__.py`, `app/utils/__init__.py` — package structure
- `app/config.py` — `Settings` via `pydantic-settings`; singleton via `@lru_cache`
- `app/models/assessment.py` — `AssessmentResult` Pydantic model; 10 GO2 + 5 GO3 fields; `ReadingLevel` Literal type alias (PEP 695)
- `app/routers/analyze.py` — `AnalyzeController`; class-based routes via `add_api_route()`; stub `/analyze` + `/health`
- `app/utils/result_consolidator.py` — stub `ResultConsolidator.merge()` raising `NotImplementedError`
- `app/dependencies.py` — stub placeholder; wired in RR-020
- `app/main.py` — app factory; `lifespan` context manager; CORS for `localhost:5173`; startup hook placeholder for RR-021
- `.env.example` — `API_KEY` template
- `requirements.txt` — added `pydantic-settings`

**Design Decisions**
- `lifespan` context manager over deprecated `@app.on_event("startup")` — cleaner ug dili mag-warn si pyright
- `X-API-Key` header uses explicit `alias=` — avoids FastAPI's underscore-to-hyphen conversion ambiguity
- `type: ignore[call-arg]` on `Settings()` — pydantic-settings reads from env, pyright dili mahibaw-an sa strict mode

**Verification**
- Pyright: `0 errors` (strict)
- SOLID: ✓ — controller handles HTTP only; no business logic; config injected via `get_settings()`
- Docs: `hld/system-overview.md`, `hld/api-layer.md`, `lld/routers/analyze-controller.md`, `lld/models/assessment.md`, `uml/class/routers.md`, `uml/class/models.md`, `uml/sequence/analyze-flow.md`, `uml/component/system-architecture.md`

---

### 2026-05-18 · Iteration 2 — RR-021 WhisperX ASR + Forced Alignment

**Added**
- `app/models/transcription.py` — `WordSegment` TypedDict + `TranscriberProtocol`; shared contract for RR-022/RR-023
- `app/services/go2/transcriber.py` — `WhisperXTranscriber` class; `load_models()` + `get_transcriber_instance()` module-level singleton

**Changed**
- `app/main.py` — filled in lifespan placeholder; now calls `load_models()` at startup
- `app/dependencies.py` — added `get_transcriber() -> TranscriberProtocol` provider

**Design Decisions**
- `WhisperXTranscriber` instance holds model refs (not raw module globals) — state lives in the object, easier to test/swap
- `_transcriber` module-level singleton kept — lifespan hook needs a single call; instance stored behind `get_transcriber_instance()`
- `TranscriberProtocol` in `app/models/` not `app/services/` — protocols/types belong in the models layer per folder contract
- All whisperx calls tagged `# type: ignore[no-untyped-call]` — whisperx has no stubs; `Any` isolated to `transcriber.py`, typed boundary at `list[WordSegment]`
- CPU device for pilot (`device="cpu"`) — swap to `"cuda"` in one place once GPU driver is stable

**Verification**
- Pyright: `0 errors` (strict)
- SOLID: ✓ — S: one class one responsibility; O: new backends implement Protocol; I: 1-method Protocol; D: `dependencies.py` returns abstraction, concrete wired there only
- Docs: `hld/go2-pipeline.md`, `lld/go2/transcriber.md`, `lld/models/transcription.md`, `uml/class/go2-classes.md`, `uml/sequence/go2-pipeline-flow.md`, `uml/class/models.md` (updated), `uml/component/system-architecture.md` (updated)

---

### 2026-05-18 · Iteration 3 — RR-022 Phil-IRI Miscue Classifier

**Added**
- `app/models/miscue.py` — `MiscueType` Literal alias, `MiscueCounts` TypedDict, `MiscueClassifierProtocol`
- `app/services/go2/miscue_classifier.py` — `MiscueClassifier`; `_levenshtein()` module-level utility; SequenceMatcher-based alignment
- `test_rr022.py` — 9 pytest unit tests covering all 7 categories + edge cases (empty transcript, repetition, all-correct)
- `docs/lld/go2/miscue-classifier.md` — LLD for `MiscueClassifier`
- `docs/lld/models/miscue.md` — LLD for `MiscueCounts` / `MiscueClassifierProtocol`

**Changed**
- `docs/uml/class/go2-classes.md` — added `MiscueClassifierProtocol`, `MiscueClassifier`, `MiscueCounts` nodes
- `docs/uml/class/models.md` — added `MiscueCounts` diagram block
- `docs/hld/go2-pipeline.md` — fixed placeholder link for `MiscueClassifier` LLD
- `requirements.txt` — added `pytest`

**Design Decisions**
- `tally: dict[str, int]` internally, `MiscueCounts(...)` constructed at return — TypedDict doesn't allow variable-key indexing in pyright strict; plain dict does; explicit construction at the end makes all keys visible to the type checker
- Repetitions detected and de-duplicated before SequenceMatcher alignment — a repeat would otherwise misalign the rest of the passage; de-duplication keeps the alignment clean
- `autojunk=False` on SequenceMatcher — default junk heuristic skips "popular" tokens (e.g. "the", "and") in longer sequences; disabled to guarantee every passage word is aligned
- `_levenshtein` as module-level function — pure, stateless; no reason to couple it to the class
- Conservative boundary: `dist ≤ 3 → mispronunciation` (not `< 3`) — SRS line 559 prefers mispronunciation over substitution on ambiguous cases; dist=3 lands in mispronunciation

**Verification**
- Pyright: `0 errors` (strict)
- Tests: `9/9 passed` (`pytest test_rr022.py`)
- SOLID: ✓ — S: classifier owns only alignment+taxonomy logic; O: `MiscueClassifierProtocol` allows new classifiers; I: 1-method Protocol; D: concrete not yet wired (deferred to RR-020 `dependencies.py`)
- Docs: `lld/go2/miscue-classifier.md`, `lld/models/miscue.md`, `uml/class/go2-classes.md` (updated), `uml/class/models.md` (updated), `hld/go2-pipeline.md` (updated)
