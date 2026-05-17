# API Layer — High-Level Design

## Purpose
The HTTP boundary of the microservice. Handles auth, file I/O, and delegation
to the service layer. Walay business logic diri.

## Responsibilities
- Validate `X-API-Key` header on every `/analyze` request
- Accept `multipart/form-data` with `file` + `passage_id`
- Delegate processing to `AnalyzeService` (wired in RR-020)
- Return `AssessmentResult` or raise structured HTTP errors

## Boundaries
- Owns: route definitions, auth check, request parsing, HTTP error responses
- Hands off to: `AnalyzeService` for all pipeline logic

## Key Design Decisions
- `AnalyzeController` class with `router.add_api_route()` — not bare `@router.post()`
- CORS locked to `http://localhost:5173` — not wildcard

## Dependencies
- `app.models.assessment.AssessmentResult`
- `app.config.Settings`

## Diagrams
| Diagram | Link |
|---|---|
| Class relationships | [routers.md](../uml/class/routers.md) |
| Request flow | [analyze-flow.md](../uml/sequence/analyze-flow.md) |

## Classes in this Domain
| Class | LLD |
|---|---|
| `AnalyzeController` | [analyze-controller.md](../lld/routers/analyze-controller.md) |
