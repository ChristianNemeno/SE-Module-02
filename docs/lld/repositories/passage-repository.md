# `PassageRepository` — Low-Level Design

## Responsibility
Fetches passage text and word count from the Supabase `passages` table by passage ID.

## Implements
[`PassageRepositoryProtocol`](../../uml/class/orchestrator-classes.md)

## Constructor Dependencies
| Parameter | Type | Injected via |
|---|---|---|
| `client` | `supabase.Client` | `dependencies.py` via `get_supabase_client()` |

## Methods
| Method | Purpose | Edge cases |
|---|---|---|
| `fetch(passage_id)` | SELECT text, word_count WHERE id = passage_id | `APIError` or empty result → `ValueError("Passage not found: ...")` |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [orchestrator-classes.md](../../uml/class/orchestrator-classes.md) |

## Related
- HLD: [go2-pipeline.md](../../hld/go2-pipeline.md)
- Source: `app/services/db/passage_repository.py`
