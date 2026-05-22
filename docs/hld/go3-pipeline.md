# GO3 Pipeline — High-Level Design

## Purpose
Analyzes the recorded reading video for behavioral signals and returns two flags:
`finger_pointing` (student points at text) and `loss_of_place` (erratic gaze movement).
Runs in parallel with GO2 via `asyncio.gather` (wired in REA-18).

## Responsibilities
- Load MediaPipe HandLandmarker + FaceLandmarker once at startup.
- Sample every 5th frame; aggregate finger-pointing ratio and gaze-shift count → binary flags.
- Return `CVFlags` dict regardless of video quality (no crash on empty/missing/short video).

## Boundaries
- Owns: `app/services/go3/cv_detector.py`, `app/models/cv_detector.py`
- Hands off to: `ResultConsolidator` (REA-24) and `AnalyzeService` orchestrator (REA-18)

## Key Design Decisions
- Uses MediaPipe **Tasks API** (HandLandmarker + FaceLandmarker IMAGE mode) — the legacy
  `mp.solutions` API was removed in mediapipe ≥ 0.10.30.
- `.task` bundles are downloaded once into a gitignored local cache
  (`app/services/go3/models/`) on first `load()` call; subsequent boots are instant.
- Singleton pattern in FastAPI `lifespan` — identical to GO2 WhisperXTranscriber.
- 120s wall-clock timeout on `detect()` guards against long videos on CPU.

## Dependencies
- `mediapipe >= 0.10.35` (Tasks API, numpy 2 compatible)
- `opencv-contrib-python` (cv2, bundled transitively via mediapipe)

## Diagrams
| Diagram | Link |
|---|---|
| System architecture | [system-architecture.md](../uml/component/system-architecture.md) |
| Class relationships | [go3-classes.md](../uml/class/go3-classes.md) |
| Dependency wiring | [dependency-graph.md](../uml/component/dependency-graph.md) |

## Classes in this Domain
| Class | LLD |
|---|---|
| `CVDetector` | [lld/go3/cv-detector.md](../lld/go3/cv-detector.md) |
| `CVDetectorProtocol` | [lld/models/cv-detector.md](../lld/models/cv-detector.md) |
| `CVFlags` | [lld/models/cv-detector.md](../lld/models/cv-detector.md) |
