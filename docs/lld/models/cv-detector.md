# `CVFlags` + `CVDetectorProtocol` — Low-Level Design

## Responsibility
Define the GO3 result shape and the interface that consumers depend on.

## `CVFlags` (TypedDict)
| Field | Type | Meaning |
|---|---|---|
| `finger_pointing` | `bool` | Index tip in text region in ≥ 20% of sampled frames |
| `loss_of_place` | `bool` | Iris x shifted > 0.15 across ≥ 3 consecutive sampled frames |

## `CVDetectorProtocol` (Protocol)
| Method | Signature | Implemented by |
|---|---|---|
| `detect` | `(video_path: str) -> CVFlags` | `CVDetector` |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [go3-classes.md](../../uml/class/go3-classes.md) |

## Related
- HLD: [go3-pipeline.md](../../hld/go3-pipeline.md)
- Source: `app/models/cv_detector.py`
