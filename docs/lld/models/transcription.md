# `WordSegment` / `TranscriberProtocol` — Low-Level Design

## Responsibility
Defines the shared data contract between the ASR layer and RR-022/RR-023: `WordSegment` is the typed dict shape every transcriber must return; `TranscriberProtocol` is the structural interface all transcribers satisfy.

## Types
| Name | Kind |
|---|---|
| `WordSegment` | `TypedDict` |
| `TranscriberProtocol` | `Protocol` |

## WordSegment Fields
| Field | Type | Notes |
|---|---|---|
| `word` | `str` | Lowercase, stripped token |
| `start` | `float` | Start time in seconds |
| `end` | `float` | End time in seconds |
| `score` | `float` | Alignment confidence (defaults to `1.0` if absent from whisperx output) |

## Diagrams
| Diagram | Link |
|---|---|
| GO2 class diagram | [go2-classes.md](../../uml/class/go2-classes.md) |
| Models diagram | [models.md](../../uml/class/models.md) |

## Related
- HLD: [go2-pipeline.md](../../hld/go2-pipeline.md)
- Source: `app/models/transcription.py`
