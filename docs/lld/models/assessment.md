# `AssessmentResult` — Low-Level Design

## Responsibility
Pydantic model returned by `/analyze`. Holds all 15 fields (10 GO2 + 5 GO3). No logic — data shape only.

## Implements
N/A — pure Pydantic `BaseModel`.

## Fields
| Field | Type | Constraint | Source |
|---|---|---|---|
| `wpm` | `float` | — | GO2 |
| `word_recognition_pct` | `float` | `ge=0, le=100` | GO2 |
| `reading_level` | `Literal[...]` | One of 3 exact strings | GO2 |
| `correct` … `refusal_to_pronounce` | `int` | — | GO2 (7 miscue counts) |
| `finger_pointing` | `bool` | — | GO3 (CVDetector) |
| `loss_of_place` | `bool` | — | GO3 (CVDetector) |
| `monotone_reading` | `bool` | — | GO3 (ProsodyAmplitudeDetector) |
| `word_by_word_reading` | `bool` | — | GO3 (ProsodyAmplitudeDetector) |
| `inaudible_reading` | `bool` | — | GO3 (ProsodyAmplitudeDetector) |

## Edge Cases
- `reading_level` must be exactly `"Frustration"`, `"Instructional"`, or `"Independent"` — Pydantic rejects all others
- `word_recognition_pct` outside 0–100 raises `ValidationError` at runtime

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [models.md](../../uml/class/models.md) |

## Related
- HLD: [system-overview.md](../../hld/system-overview.md)
- Source: `app/models/assessment.py`
