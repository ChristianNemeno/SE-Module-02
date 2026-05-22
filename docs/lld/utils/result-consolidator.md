# `ResultConsolidator` — Low-Level Design

## Responsibility
Merges GO2 and GO3 output dicts into one validated `AssessmentResult`, raising `ValueError` if any of the 15 required fields are absent or `None`.

## Implements
N/A — utility class, no Protocol.

## Constructor Dependencies
None — all methods are `@staticmethod`.

## Methods
| Method | Purpose | Edge cases |
|---|---|---|
| `merge(go2_result, go3_result)` | Merges dicts, validates 15 required fields, returns `AssessmentResult` | Missing/`None` field → `ValueError` listing the offenders |

## Constants
| Constant | Contents |
|---|---|
| `REQUIRED_GO2_FIELDS` | 10 fields: `wpm`, `word_recognition_pct`, `reading_level`, 7 miscue counts |
| `REQUIRED_GO3_FIELDS` | 5 fields: `finger_pointing`, `loss_of_place`, `monotone_reading`, `word_by_word_reading`, `inaudible_reading` |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [models.md](../../uml/class/models.md) |
| System architecture | [system-architecture.md](../../uml/component/system-architecture.md) |

## Related
- HLD: [system-overview.md](../../hld/system-overview.md)
- Source: `app/utils/result_consolidator.py`
