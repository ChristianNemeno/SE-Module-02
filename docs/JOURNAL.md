# Dev Journal — ReadRight GO2

> Append-only log of each build iteration. Newest entries at the bottom.

---

### 2026-05-19 · Iteration 5 — RR-045 Deployment Infrastructure

**Added**
- `app/routers/health.py` — `HealthController`; extracted from `AnalyzeController`; no auth, liveness probe only
- `Dockerfile` — `python:3.12-slim`; installs ffmpeg; pre-downloads `large-v3` into HuggingFace cache at build time; `HEALTHCHECK` on `/health`
- `.dockerignore` — excludes `.venv`, `.env`, `__pycache__`, `tests/`, `docs/`
- `.github/workflows/deploy.yml` — 3-job CI/CD: pyright + pytest → GHCR push → SSH deploy to Droplet
- `docs/deploy-plan.md` — full deployment plan and Droplet setup guide

**Changed**
- `app/config.py` — added `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `ALLOWED_ORIGINS: list[str]`
- `app/main.py` — CORS origins now read from `settings.ALLOWED_ORIGINS`; wires in `HealthController`
- `app/routers/analyze.py` — removed `/health` route and method (SRP fix); `AnalyzeController` now owns only `/analyze`
- `.env.example` — replaced `SUPABASE_ANON_KEY` with `SUPABASE_SERVICE_KEY`; added `ALLOWED_ORIGINS`
- `pyrightconfig.json` — removed `venvPath`/`venv` so pyright works in CI without `.venv`
- `issues.md` — cleared completed GO2 issues; replaced with pointer to `CLAUDE.md`

**Design Decisions**
- GHCR over DO Container Registry — free, uses `GITHUB_TOKEN` in Actions (no extra secret for build/push), only needs a `GHCR_PAT` on the Droplet for pulls
- `ALLOWED_ORIGINS: list[str]` defaulting to `["http://localhost:5173"]` — pydantic-settings parses JSON arrays natively; prod sets `["https://readright.app"]` in `/etc/readright/env`
- `SUPABASE_SERVICE_KEY` defaults to `""` — making it required would break existing tests that don't set it; enforce non-empty once Supabase calls are wired in RR-020
- Deploy step uses `envs:` in `appleboy/ssh-action` to pass `GHCR_PAT` — avoids interpolating secrets directly into shell `run:` blocks (security hook requirement)

**Verification**
- Pyright: `0 errors` (strict)
- SOLID: ✓ `HealthController` extracted as SRP fix; `AnalyzeController` now single-responsibility

---

### 2026-05-22 · Iteration 6 — REA-22 / RR-030 GO3 CVDetector (MediaPipe)

**Added**
- `app/models/cv_detector.py` — `CVFlags` TypedDict + `CVDetectorProtocol`; GO3 result shape and interface
- `app/services/go3/cv_detector.py` — `CVDetector` singleton; loads HandLandmarker + FaceLandmarker; samples every 5th frame; 120s timeout; always returns valid dict
- `tests/test_rr030.py` — 5 tests: 2 real-clip (skip until fixture videos provided), 3 generated-edge-case (blank video, 1-frame, timeout monkeypatch)
- `docs/hld/go3-pipeline.md`, `docs/lld/go3/cv-detector.md`, `docs/lld/models/cv-detector.md` — GO3 domain docs
- `docs/uml/class/go3-classes.md`, `docs/uml/component/dependency-graph.md` — new UML diagrams

**Changed**
- `app/main.py` — lifespan now calls `load_cv_models()` alongside `load_models()` (aliased import)
- `app/dependencies.py` — added `get_cv_detector()` provider returning `CVDetectorProtocol` singleton
- `docs/uml/component/system-architecture.md` — added REA-22 current-state diagram (GO2 ✓, GO3 partial)
- `.gitignore` — added `app/services/go3/models/` (downloaded .task bundles, not committed)

**Design Decisions**
- MediaPipe Tasks API instead of legacy `mp.solutions` — `mp.solutions` was removed in mediapipe 0.10.30+; Tasks API (HandLandmarker + FaceLandmarker) is the current stable surface and supports numpy 2
- Download .task bundles at `load()` rather than committing them — keeps repo light (~11 MB); cached after first run; aligns with how the app will run in prod (Docker build can pre-download)
- Module-scoped pytest fixture for CVDetector — deviation from GO2's function-scoped convention; load() is expensive (model init + file I/O) so one fixture per module is correct here
- `_TIMEOUT_SECONDS` as a module-level constant (not a default arg) — required so monkeypatch can override it in `test_timeout_returns_defaults`

**Verification**
- Pyright: `0 errors` (strict, `pyright app/`)
- Tests: `21 passed, 2 skipped` — real-clip tests skip cleanly until fixture videos added
- SOLID: ✓ CVDetector single-responsibility (inference only); CVDetectorProtocol narrow (1 method); concrete wired only in `dependencies.py`
- Docs: `hld/go3-pipeline.md`, `lld/go3/cv-detector.md`, `lld/models/cv-detector.md`, `uml/class/go3-classes.md`, `uml/component/dependency-graph.md`, `uml/component/system-architecture.md`

---

### 2026-05-22 · Iteration 7 — REA-23 / RR-031 GO3 ProsodyAmplitudeDetector

**Added**
- `app/models/prosody_detector.py` — `ProsodyFlags` TypedDict + `ProsodyDetectorProtocol`; GO3 audio result shape and interface
- `app/services/go3/prosody_detector.py` — `ProsodyAmplitudeDetector`; stateless; extracts `inaudible_reading` (RMS), `monotone_reading` (F0 std-dev), `word_by_word_reading` (IOI) from WAV
- `docs/lld/go3/prosody-detector.md`, `docs/lld/models/prosody-detector.md` — LLD for new class + protocol

**Changed**
- `app/dependencies.py` — added `get_prosody_detector()` per-call provider (stateless, no singleton needed)
- `docs/hld/go3-pipeline.md` — updated to include `ProsodyAmplitudeDetector` + new deps (librosa, parselmouth)
- `docs/uml/class/go3-classes.md` — added `ProsodyDetectorProtocol`, `ProsodyAmplitudeDetector`, `ProsodyFlags`
- `docs/uml/component/dependency-graph.md` — added `get_prosody_detector` edge

**Design Decisions**
- Per-call instantiation (like `ScoringEngine`) instead of singleton — `ProsodyAmplitudeDetector` holds no model state; librosa/parselmouth load lazily per call; singleton overhead unnecessary
- `parselmouth` calls isolated with `# type: ignore[no-untyped-call]` + `Any` annotation — library has no stubs; same pattern as mediapipe in `cv_detector.py`
- Audio < 5s returns all-False immediately — too short for reliable F0/onset analysis; avoids divide-by-zero and false positives on near-silent clips

**Verification**
- Pyright: `0 errors` (strict)
- SOLID: ✓ single responsibility (audio prosody flags only); `ProsodyDetectorProtocol` narrow (1 method); concrete wired only in `dependencies.py`
- Docs: `hld/go3-pipeline.md`, `lld/go3/prosody-detector.md`, `lld/models/prosody-detector.md`, `uml/class/go3-classes.md`, `uml/component/dependency-graph.md`

---

### 2026-05-22 · Iteration 8 — REA-24 / RR-032 ResultConsolidator

**Added**
- `app/utils/result_consolidator.py` — `ResultConsolidator.merge()` implemented; validates all 15 required fields are present and non-`None`; returns `AssessmentResult.model_validate(merged)` for Pydantic type safety
- `tests/test_rr032.py` — 3 tests: valid merge → `AssessmentResult`, missing field → `ValueError`, `None` field → `ValueError`
- `docs/lld/utils/result-consolidator.md` — LLD for `ResultConsolidator`

**Changed**
- `app/models/assessment.py` — replaced stale GO3 fields (`lip_movement`, `head_movement`, `voice_too_soft`, `loses_place`) with the correct fields matching actual detector outputs: `loss_of_place`, `monotone_reading`, `word_by_word_reading`, `inaudible_reading`
- `app/routers/analyze.py` — stub `AssessmentResult(...)` updated to use corrected GO3 field names
- `docs/lld/models/assessment.md` — updated field table to reflect correct GO3 fields with source (CVDetector vs ProsodyAmplitudeDetector)
- `docs/uml/class/models.md` — updated `AssessmentResult` class diagram; added `ResultConsolidator` block
- `docs/uml/component/system-architecture.md` — added REA-24 current-state diagram showing `ResultConsolidator` wired between GO2/GO3 and controller

**Design Decisions**
- `@staticmethod` on `merge` — no instance state; avoids forcing caller to instantiate `ResultConsolidator` just to call the one method
- `AssessmentResult.model_validate(merged)` over `AssessmentResult(**merged)` — `model_validate` accepts `Any`, avoiding pyright strict complaints about unpacking `dict[str, Any]` into a typed constructor
- Pre-validation before `model_validate` — catches missing/`None` fields with a clear `ValueError` message before Pydantic's own `ValidationError` fires; consistent with Linear issue spec

**Verification**
- Pyright: `0 errors` (strict)
- Tests: `3/3 passed` (`pytest tests/test_rr032.py`)
- SOLID: ✓ — S: `ResultConsolidator` owns only merge + validation; no GO2/GO3 coupling; D: depends on `AssessmentResult` model, not on any concrete service
- Docs: `lld/utils/result-consolidator.md`, `lld/models/assessment.md` (updated), `uml/class/models.md` (updated), `uml/component/system-architecture.md` (updated)

---

### 2026-05-23 · Iteration 9 — REA-18 / RR-020 Real `/analyze` Orchestrator

**Added**
- `app/models/passage.py` — `PassageRecord` TypedDict + `PassageRepositoryProtocol`; passage fetch contract
- `app/models/session.py` — `SessionRecord` TypedDict (17 fields) + `SessionRepositoryProtocol`; session persistence contract
- `app/models/media_extractor.py` — `ExtractionResult` TypedDict + `MediaExtractorProtocol`; ffmpeg extraction contract
- `app/models/pipeline_results.py` — `GO2Result` (10 fields) + `GO3Result` (5 bool fields); internal pipeline output shapes
- `app/services/db/__init__.py` — empty package marker
- `app/services/db/supabase_client.py` — module-level `_client` singleton; `init_supabase_client()` + `get_supabase_client()`; no-op if creds blank
- `app/services/db/passage_repository.py` — `PassageRepository.fetch()`; SELECT from `passages` table; raises `ValueError` on missing row
- `app/services/db/session_repository.py` — `SessionRepository.insert()`; INSERT into `sessions` table; lets `APIError` propagate
- `app/services/media_extractor.py` — `MediaExtractor.extract()`; two `subprocess.run` ffmpeg calls → WAV (16kHz mono) + MP4 (libx264); raises `RuntimeError` on `CalledProcessError`
- `app/services/go2/pipeline.py` — `GO2Pipeline.run()`; chains `passage_repo.fetch → transcribe → classify → score → GO2Result`
- `app/services/go3/pipeline.py` — `GO3Pipeline.run()`; chains `cv_detector.detect + prosody_detector.detect → GO3Result`
- `app/services/analysis_orchestrator.py` — `AnalysisOrchestrator.run()`; full async pipeline: temp file → extract → `asyncio.gather(GO2, GO3)` → `ResultConsolidator.merge` → optional DB insert
- `tests/conftest.py` — seeds `API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` before any app import
- `tests/test_rr020.py` — 8 integration tests covering: 200+all-16-fields, 401 bad key, 422 missing field, 500 ffmpeg, 200+db_save_failed, learner_id skip, learner_id passthrough, webm+mp4 both accepted

**Changed**
- `app/config.py` — added `extra="ignore"` to `model_config` so test imports survive without full `.env`
- `app/models/assessment.py` — added `db_save_failed: bool = False` (16th field)
- `app/dependencies.py` — added 6 new providers: `get_passage_repository`, `get_session_repository`, `get_media_extractor`, `get_go2_pipeline`, `get_go3_pipeline`, `get_analysis_orchestrator`
- `app/main.py` — lifespan now calls `asyncio.to_thread(init_supabase_client)`; added module-level `_pipeline_error_handler` that unwraps `{"error", "code"}` dict from HTTPException detail
- `app/routers/analyze.py` — replaced stub; real `AnalysisOrchestrator` injected via `Depends`; accepts optional `learner_id: str = Form("")`
- `tests/test_rr032.py` — `len(result.model_dump()) == 15` → `== 16`

**Design Decisions**
- Skip DB insert in orchestrator (not repository) when `learner_id` blank — ensures both real and fake repos are bypassed in tests; avoids leaking policy into the persistence layer
- `db_save_failed=True` → HTTP 200 (not 500) — DB unavailability is non-fatal; learner still gets results; frontend retries persist on reconnect
- `_pipeline_error_handler` at module level (not nested in `create_app`) — avoids pyright `reportUnusedFunction` on a nested function referenced only by a decorator call
- `ExtractionResult` as `TypedDict` (not `dataclass`) — accessed by `dict` key downstream in `asyncio.gather` unpacking; TypedDict is the right shape for key-subscript access patterns
- `asyncio.to_thread` for all blocking calls — keeps the event loop free; ffmpeg, WhisperX, MediaPipe, and Supabase are all blocking/sync

**Verification**
- Pyright: `0 errors` (strict, `pyright app/`)
- Tests: `34/34 passed` (`pytest tests/test_rr020.py tests/test_rr022.py tests/test_rr023.py tests/test_rr030.py tests/test_rr032.py`)
- SOLID: ✓ — S: `AnalysisOrchestrator` orchestrates only; `MediaExtractor` extracts only; each repo persists one entity; O: all injected via Protocols; D: concretes wired only in `dependencies.py`
- Docs: `hld/api-layer.md` (updated), `lld/go2/go2-pipeline.md`, `lld/go3/go3-pipeline.md`, `lld/services/analysis-orchestrator.md`, `lld/services/media-extractor.md`, `lld/repositories/passage-repository.md`, `lld/repositories/session-repository.md`, `lld/models/passage.md`, `lld/models/session.md`, `lld/models/media-extractor-model.md`, `lld/models/pipeline-results.md`, `uml/class/models.md` (updated), `uml/class/go2-classes.md` (updated), `uml/class/go3-classes.md` (updated), `uml/class/orchestrator-classes.md`, `uml/sequence/analyze-flow.md` (updated), `uml/sequence/go3-pipeline-flow.md`, `uml/component/system-architecture.md` (updated), `uml/component/dependency-graph.md` (updated)

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

---

### 2026-05-18 · Iteration 4 — RR-023 WPM + Scoring + Reading Level

**Added**
- `app/models/scoring.py` — `ScoringResult` TypedDict (`wpm`, `word_recognition_pct`, `reading_level`) + `ScoringEngineProtocol`
- `app/services/go2/scoring_engine.py` — `ScoringEngine`; `score()` public method + `_wpm()` / `_word_recognition_pct()` / `_reading_level()` private helpers; module-level constants `_INDEPENDENT_MIN_PCT=97.0`, `_INSTRUCTIONAL_MIN_PCT=91.0`
- `tests/test_rr023.py` — 9 pytest unit tests covering all three thresholds, boundary ties, empty transcript, zero-passage-words, zero-duration audio (18/18 assertions passing)
- `docs/lld/go2/scoring-engine.md` — LLD for `ScoringEngine`
- `docs/lld/models/scoring.md` — LLD for `ScoringResult` / `ScoringEngineProtocol`

**Changed**
- `app/dependencies.py` — added `get_scoring_engine() -> ScoringEngineProtocol` provider (per-call instantiation; cheap, stateless)
- `docs/uml/class/go2-classes.md` — added `ScoringEngineProtocol`, `ScoringEngine`, `ScoringResult` nodes + `implements` and `returns` edges
- `docs/uml/class/models.md` — added `ScoringResult` diagram block
- `docs/hld/go2-pipeline.md` — removed `*(RR-023)*` placeholder marker; extended Key Design Decisions with boundary-rule + stateless-engine notes

**Design Decisions**
- Boundary rule resolved to `>=` per CLAUDE.md (Independent ≥97, Instructional ≥91) — this overrides the SRS line-633 "ties go to lower" wording; CLAUDE.md is the canonical spec for this module and the test fixtures encode `>=`
- `ScoringEngine` is per-request, not a startup singleton — no models, no I/O, no cached state; constructor takes no args; `get_scoring_engine()` returns a fresh instance per FastAPI call
- Error set = `mispronunciation + substitution + omission + refusal_to_pronounce` — `insertion` and `repetition` are explicitly excluded per Phil-IRI (extra words and stutters don't penalize recognition %)
- `_wpm` uses `total_passage_words / duration * 60` (not transcript word count) — matches SRS formula; reflects intended reading pace against the reference passage rather than rewarding insertions
- Three edge cases collapse to `0.0`: empty transcript, `total_passage_words == 0`, and `duration <= 0` (single-word or out-of-order timestamps) — keeps `score()` total and avoids `ZeroDivisionError`
- Thresholds as module-level `_PRIVATE` constants (not class attrs) — single source of truth, no risk of subclass override changing scoring semantics

**Verification**
- Pyright: `0 errors` (strict)
- Tests: `9/9 passed` (`pytest tests/test_rr023.py`); 18/18 assertions
- SOLID: ✓ — S: engine owns only score math; O: `ScoringEngineProtocol` allows alternative scorers; I: 1-method Protocol; D: `dependencies.py` returns the abstraction, concrete wired there
- Docs: `lld/go2/scoring-engine.md`, `lld/models/scoring.md`, `uml/class/go2-classes.md` (updated), `uml/class/models.md` (updated), `hld/go2-pipeline.md` (updated)
