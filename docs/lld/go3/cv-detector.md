# `CVDetector` — Low-Level Design

## Responsibility
Load MediaPipe Hand + Face landmarkers at startup and run per-video inference to produce GO3 behavioral flags.

## Implements
[`CVDetectorProtocol`](../../uml/class/go3-classes.md)

## Constructor Dependencies
None — instantiated by `load_models()`, not via FastAPI `Depends()`.

## Methods
| Method | Purpose | Edge cases |
|---|---|---|
| `load()` | Downloads .task bundles if absent; builds HandLandmarker + FaceLandmarker | Network error → raises; already cached → instant |
| `detect(video_path)` | Samples every 5th frame, returns `CVFlags` | Missing/empty video → `{False, False}`; > 120s → early exit `{False, False}` |
| `_finger_in_text_region(image)` | Index-tip (landmark 8) inside lower-center region? | No hand detected → `False` |
| `_iris_x(image)` | Normalized x of left iris (landmark 468) | No face detected → `None` |

## Module-level helpers
| Symbol | Purpose |
|---|---|
| `load_models()` | Instantiates + loads singleton; called in FastAPI lifespan |
| `get_detector_instance()` | Returns singleton; raises `RuntimeError` if not loaded |
| `_ensure_model(path, url)` | Downloads .task bundle to local cache if not present |
| `_default_flags()` | Returns `{"finger_pointing": False, "loss_of_place": False}` |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [go3-classes.md](../../uml/class/go3-classes.md) |
| System architecture | [system-architecture.md](../../uml/component/system-architecture.md) |

## Related
- HLD: [go3-pipeline.md](../../hld/go3-pipeline.md)
- Source: `app/services/go3/cv_detector.py`
