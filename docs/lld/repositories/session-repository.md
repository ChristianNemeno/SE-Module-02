# `SessionRepository` — Low-Level Design

## Responsibility
Persists a completed assessment session to the Supabase `sessions` table.

## Implements
[`SessionRepositoryProtocol`](../../uml/class/orchestrator-classes.md)

## Constructor Dependencies
| Parameter | Type | Injected via |
|---|---|---|
| `client` | `supabase.Client` | `dependencies.py` via `get_supabase_client()` |

## Methods
| Method | Purpose | Edge cases |
|---|---|---|
| `insert(record)` | INSERT all 17 SessionRecord fields into `sessions` | `APIError` propagates to caller (orchestrator catches and sets `db_save_failed=True`); blank `learner_id` is guarded at orchestrator level |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [orchestrator-classes.md](../../uml/class/orchestrator-classes.md) |
| Sequence flow | [analyze-flow.md](../../uml/sequence/analyze-flow.md) |

## Related
- HLD: [api-layer.md](../../hld/api-layer.md)
- Source: `app/services/db/session_repository.py`
