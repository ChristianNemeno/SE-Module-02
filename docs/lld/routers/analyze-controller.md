# `AnalyzeController` — Low-Level Design

## Responsibility
Handles HTTP for `POST /analyze` and `GET /health` — auth, request parsing,
response formatting. Walay pipeline logic.

## Implements
No Protocol yet — wired directly in `app/main.py` for RR-004.

## Constructor Dependencies
None injected — stub only. `AnalyzeService` will be injected via `Depends()` in RR-020.

## Methods
| Method | Purpose | Edge cases |
|---|---|---|
| `analyze(file, passage_id, x_api_key)` | Returns stub `AssessmentResult` after auth check | Invalid key → 401 |
| `health()` | Liveness probe | Always returns `{"status": "ok"}` |
| `_check_api_key(key)` | Compares key against `Settings.API_KEY` | Raises `HTTPException(401)` on mismatch |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [routers.md](../../uml/class/routers.md) |
| Sequence / flow | [analyze-flow.md](../../uml/sequence/analyze-flow.md) |

## Related
- HLD: [api-layer.md](../../hld/api-layer.md)
- Source: `app/routers/analyze.py`
