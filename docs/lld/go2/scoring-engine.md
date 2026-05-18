# `ScoringEngine` — Low-Level Design

## Responsibility
Computes the three Phil-IRI scoring fields — WPM, word recognition %, and reading level — from aligned transcript word timings and miscue counts.

## Implements
[`ScoringEngineProtocol`](../../uml/class/go2-classes.md)

## Constructor Dependencies
None — stateless, per-request instance.

## Methods
| Method | Purpose | Edge cases |
|---|---|---|
| `score(transcript_words, miscue_counts, total_passage_words)` | Builds the `ScoringResult` from word timings + miscue counts | Empty transcript / `total == 0` → `wpm=0.0`, `pct=0.0`, `reading_level="Frustration"` |
| `_wpm(words, total_passage_words)` | `total_passage_words / duration * 60`; duration = `last.end - first.start` | Empty list, zero total, or `duration <= 0` → `0.0` |
| `_word_recognition_pct(counts, total)` | `(total - errors) / total * 100`; errors = mispron + sub + omission + refusal | `total == 0` → `0.0`; errors exceeding total are not clamped (caller responsibility) |
| `_reading_level(pct)` | Threshold lookup: ≥97 Independent, ≥91 Instructional, else Frustration | Boundary uses `>=`; ties resolve to the higher classification |

## Module-Level Constants
| Constant | Value | Purpose |
|---|---|---|
| `_INDEPENDENT_MIN_PCT` | `97.0` | Lower bound for `Independent` reading level |
| `_INSTRUCTIONAL_MIN_PCT` | `91.0` | Lower bound for `Instructional` reading level |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [go2-classes.md](../../uml/class/go2-classes.md) |
| Pipeline flow | [go2-pipeline-flow.md](../../uml/sequence/go2-pipeline-flow.md) |

## Related
- HLD: [go2-pipeline.md](../../hld/go2-pipeline.md)
- Source: `app/services/go2/scoring_engine.py`
