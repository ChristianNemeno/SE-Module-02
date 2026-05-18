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
| `MiscueClassifierProtocol` | `Protocol` | Interface the pipeline depends on; concrete wired in `dependencies.py` at RR-020 |

## Diagrams
| Diagram | Link |
|---|---|
| Models class diagram | [models.md](../../uml/class/models.md) |
| GO2 class diagram | [go2-classes.md](../../uml/class/go2-classes.md) |

## Related
- HLD: [go2-pipeline.md](../../hld/go2-pipeline.md)
- Source: `app/models/miscue.py`
