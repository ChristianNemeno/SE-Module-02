# `SessionRecord` + `SessionRepositoryProtocol` — Low-Level Design

## Responsibility
Data shape and persistence contract for a completed assessment session.

## Implements
[Models diagram](../../uml/class/models.md)

## Fields — SessionRecord
| Field | Type | Notes |
|---|---|---|
| `learner_id` | `str` | UUID string; blank string skips insert (guarded by orchestrator) |
| `passage_id` | `str` | Foreign key to `passages` table |
| `wpm` | `float` | |
| `word_recognition_pct` | `float` | |
| `reading_level` | `str` | |
| `correct` … `refusal_to_pronounce` | `int` | 7 miscue count fields |
| `finger_pointing` … `inaudible_reading` | `bool` | 5 behavioral flags |

## Methods — SessionRepositoryProtocol
| Method | Purpose | Edge cases |
|---|---|---|
| `insert(record)` | Persist session to DB | Raises `Exception` on DB error (non-fatal in orchestrator) |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [models.md](../../uml/class/models.md) |

## Related
- HLD: [api-layer.md](../../hld/api-layer.md)
- Source: `app/models/session.py`
