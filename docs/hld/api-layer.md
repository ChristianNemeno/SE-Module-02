# API Layer — High-Level Design

## Purpose
The HTTP boundary of the microservice. Handles auth, file I/O, and delegation to `AnalysisOrchestrator`. No business logic here.

## Responsibilities
- Validate `X-API-Key` header on every `/analyze` request
- Accept `multipart/form-data` with `file`, `passage_id`, and optional `learner_id`
- Delegate processing to `AnalysisOrchestrator`
- Return `AssessmentResult` (16 fields incl. `db_save_failed`) or structured HTTP errors

## Boundaries
- Owns: route definitions, auth check, request parsing, HTTP error shape
- Hands off to: `AnalysisOrchestrator` for all pipeline + persistence logic

## Key Design Decisions
- `AnalyzeController` class with `router.add_api_route()` — not bare `@router.post()`
- Custom `_pipeline_error_handler` returns raw `{"error", "code"}` — not FastAPI's default `{"detail": ...}` wrapper
- DB write failure → HTTP 200 with `db_save_failed=True` (non-fatal); pipeline failure → HTTP 500 `PIPELINE_FAILED`
- All blocking work (ffmpeg, WhisperX, MediaPipe, Supabase) runs in `asyncio.to_thread`
- `learner_id` is optional (`Form("")`) — blank skips DB insert entirely

## Dependencies
- `app.models.assessment.AssessmentResult`
- `app.config.Settings`
- `app.services.analysis_orchestrator.AnalysisOrchestrator`
- `app.services.db.supabase_client` (init at startup in lifespan)

## Diagrams
| Diagram | Link |
|---|---|
| Class relationships | [routers.md](../uml/class/routers.md) |
| Orchestrator classes | [orchestrator-classes.md](../uml/class/orchestrator-classes.md) |
| Request flow | [analyze-flow.md](../uml/sequence/analyze-flow.md) |
| System architecture | [system-architecture.md](../uml/component/system-architecture.md) |
| Dependency wiring | [dependency-graph.md](../uml/component/dependency-graph.md) |

## Classes in this Domain
| Class | LLD |
|---|---|
| `AnalyzeController` | [analyze-controller.md](../lld/routers/analyze-controller.md) |
| `AnalysisOrchestrator` | [analysis-orchestrator.md](../lld/services/analysis-orchestrator.md) |
| `MediaExtractor` | [media-extractor.md](../lld/services/media-extractor.md) |
| `PassageRepository` | [passage-repository.md](../lld/repositories/passage-repository.md) |
| `SessionRepository` | [session-repository.md](../lld/repositories/session-repository.md) |
