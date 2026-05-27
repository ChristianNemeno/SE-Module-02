# `MiscueCounts` / `MiscueClassifierProtocol` — Low-Level Design

## Responsibility
Defines the output shape for GO2 miscue classification and the protocol interface consumed by the pipeline.

## Implements
N/A — data shape and protocol definition only.

## Constructor Dependencies
N/A

## Types
| Name | Kind | Purpose |
|---|---|---|
| `MiscueType` | `Literal` type alias | The 7 valid miscue label strings |
| `MiscueCounts` | `TypedDict` | Per-category count dict returned by `MiscueClassifier.classify()` |
| `MiscueDetail` | `TypedDict` | One aligned word decision: `miscue_type`, `passage_word`/`transcript_word` (either may be `None`), `start`/`end` timing (`None` when no spoken word) |
| `MiscueClassifierProtocol` | `Protocol` | Interface the pipeline depends on; `classify()` + `detail()`, both accept optional `proper_nouns: list[str]`; concrete wired in `dependencies.py` |
| `MiscueReporterProtocol` | `Protocol` | Interface for printing `MiscueDetail`s after analysis; concrete (`MiscueReporter`) wired in `dependencies.py` |

## Diagrams
| Diagram | Link |
|---|---|
| Models class diagram | [models.md](../../uml/class/models.md) |
| GO2 class diagram | [go2-classes.md](../../uml/class/go2-classes.md) |

## Related
- HLD: [go2-pipeline.md](../../hld/go2-pipeline.md)
- Source: `app/models/miscue.py`
