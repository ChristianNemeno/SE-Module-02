# `MiscueReporter` — Low-Level Design

## Responsibility
Prints the full per-word breakdown to the console after GO2 analysis — every aligned decision, correct words included. Diagnostic only — does not affect the API response, DB, or scoring.

## Implements
[`MiscueReporterProtocol`](../../uml/class/go2-classes.md)

## Constructor Dependencies
None — stateless, no injected dependencies.

## Methods
| Method | Purpose | Notes |
|---|---|---|
| `report(passage_id, details)` | Prints a header (word total + miscue count) + one line per `MiscueDetail`, correct included | Uses `print()` (stdout), not `logging` — guaranteed visible under uvicorn |
| `_format(detail)` | Builds one aligned line: category, passage word, heard word, timing | — |
| `_word(word)` | Quotes a word, or `—` when `None` (omission/insertion) | — |
| `_timing(start, end)` | `1.23s–1.45s`, or `—` when timing absent (omission) | — |

## Output shape
```
=== Word breakdown for p001 (8 words, 3 miscues) ===
[correct             ] passage='the'    heard='the'  (0.00s–0.40s)
[mispronunciation    ] passage='big'    heard='cot'  (0.70s–1.10s)
[omission            ] passage='sat'    heard=—      (—)
[insertion           ] passage=—        heard='um'   (1.10s–1.40s)
[repetition          ] passage=—        heard='the'  (0.40s–0.70s)
```
Records print in passage order; repetitions trail at the end (dedup precedes alignment).
Printed to **stdout** — the uvicorn terminal locally, or container/platform logs in deployment.

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [go2-classes.md](../../uml/class/go2-classes.md) |
| Pipeline flow | [go2-pipeline-flow.md](../../uml/sequence/go2-pipeline-flow.md) |

## Related
- HLD: [go2-pipeline.md](../../hld/go2-pipeline.md)
- Source: `app/services/go2/miscue_reporter.py`
