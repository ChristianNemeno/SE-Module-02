# `GO2Result` + `GO3Result` — Low-Level Design

## Responsibility
Internal pipeline output shapes; never exposed directly in the API response.

## Implements
[Models diagram](../../uml/class/models.md)

## Fields — GO2Result
| Field | Type |
|---|---|
| `wpm` | `float` |
| `word_recognition_pct` | `float` |
| `reading_level` | `str` |
| `correct` … `refusal_to_pronounce` | `int` (7 fields) |

## Fields — GO3Result
| Field | Type |
|---|---|
| `finger_pointing` | `bool` |
| `loss_of_place` | `bool` |
| `monotone_reading` | `bool` |
| `word_by_word_reading` | `bool` |
| `inaudible_reading` | `bool` |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [models.md](../../uml/class/models.md) |

## Related
- HLD: [go2-pipeline.md](../../hld/go2-pipeline.md)
- HLD: [go3-pipeline.md](../../hld/go3-pipeline.md)
- Source: `app/models/pipeline_results.py`
