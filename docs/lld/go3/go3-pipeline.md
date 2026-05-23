# `GO3Pipeline` — Low-Level Design

## Responsibility
Runs CV detection and prosody detection in sequence and packages results into GO3Result.

## Implements
[`GO3Pipeline`](../../uml/class/go3-classes.md)

## Constructor Dependencies
| Parameter | Type | Injected via |
|---|---|---|
| `cv_detector` | `CVDetectorProtocol` | `dependencies.py` |
| `prosody_detector` | `ProsodyDetectorProtocol` | `dependencies.py` |

## Methods
| Method | Purpose | Edge cases |
|---|---|---|
| `run(mp4_path, wav_path)` | Detect CV flags + prosody flags → return merged GO3Result | Both detectors run independently; exceptions propagate to orchestrator |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [go3-classes.md](../../uml/class/go3-classes.md) |
| Sequence flow | [go3-pipeline-flow.md](../../uml/sequence/go3-pipeline-flow.md) |

## Related
- HLD: [go3-pipeline.md](../../hld/go3-pipeline.md)
- Source: `app/services/go3/pipeline.py`
