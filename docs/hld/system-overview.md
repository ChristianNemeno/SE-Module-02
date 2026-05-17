# System Overview — High-Level Design

## Purpose
ReadRight GO2 is a FastAPI microservice that accepts a learner's recorded reading
session (video/audio), runs it through an ASR + miscue classification pipeline,
and returns a Phil-IRI assessment result. GO3 runs in parallel for behavioral flags.

## Responsibilities
- Accept and validate multipart video uploads via `POST /analyze`
- Orchestrate GO2 (audio scoring) and GO3 (behavioral CV) pipelines in parallel
- Persist results to Supabase `sessions` table
- Return a complete `AssessmentResult` — no null fields

## Boundaries
- Owns: HTTP routing, pipeline orchestration, Supabase writes
- Does NOT own: frontend rendering, learner auth (JWT), passage content management

## Key Design Decisions
- Class-based controllers over bare FastAPI route functions — SRP enforced
- All concrete classes wired in `dependencies.py` — DIP enforced
- `pydantic-settings` for config — no raw `os.environ` calls in app logic

## Dependencies
- FastAPI, Uvicorn, Pydantic v2, pydantic-settings
- WhisperX (RR-021), MediaPipe (GO3), Supabase Python SDK

## Diagrams
| Diagram | Link |
|---|---|
| Component / architecture | [system-architecture.md](../uml/component/system-architecture.md) |
| Request flow | [analyze-flow.md](../uml/sequence/analyze-flow.md) |

## Domains
| Domain | HLD |
|---|---|
| API layer | [api-layer.md](api-layer.md) |
| GO2 Pipeline | *(RR-021/022/023)* |
| GO3 Pipeline | *(future)* |
