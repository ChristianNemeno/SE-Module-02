# `GO2Pipeline` — Low-Level Design

## Responsibility
Coordinates ASR transcription, miscue classification, and WPM scoring for a single reading session.

## Implements
[`GO2Pipeline`](../../uml/class/go2-classes.md)

## Constructor Dependencies
| Parameter | Type | Injected via |
|---|---|---|
| `transcriber` | `TranscriberProtocol` | `dependencies.py` |
| `classifier` | `MiscueClassifierProtocol` | `dependencies.py` |
| `scorer` | `ScoringEngineProtocol` | `dependencies.py` |
| `passage_repo` | `PassageRepositoryProtocol` | `dependencies.py` |

## Methods
| Method | Purpose | Edge cases |
|---|---|---|
| `run(wav_path, passage_id)` | Fetch passage → transcribe → classify → score → return GO2Result | Raises `ValueError` if passage not found; propagates transcriber/classifier exceptions |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [go2-classes.md](../../uml/class/go2-classes.md) |
| Sequence flow | [go2-pipeline-flow.md](../../uml/sequence/go2-pipeline-flow.md) |

## Related
- HLD: [go2-pipeline.md](../../hld/go2-pipeline.md)
- Source: `app/services/go2/pipeline.py`
