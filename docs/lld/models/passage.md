# `PassageRecord` + `PassageRepositoryProtocol` — Low-Level Design

## Responsibility
Data shape and fetch contract for Phil-IRI passage records.

## Implements
[Models diagram](../../uml/class/models.md)

## Fields — PassageRecord
| Field | Type | Notes |
|---|---|---|
| `text` | `str` | Full passage text for transcription alignment |
| `word_count` | `int` | Pre-computed for WPM calculation |

## Methods — PassageRepositoryProtocol
| Method | Purpose | Edge cases |
|---|---|---|
| `fetch(passage_id)` | Retrieve passage by ID | Raises `ValueError` if not found |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [models.md](../../uml/class/models.md) |

## Related
- HLD: [go2-pipeline.md](../../hld/go2-pipeline.md)
- Source: `app/models/passage.py`
