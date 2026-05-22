# GO3 Pipeline — High-Level Design

## Purpose
Analyzes the recorded reading session for behavioral signals via two parallel detectors:
`CVDetector` (video — finger pointing + gaze) and `ProsodyAmplitudeDetector` (audio — volume, pitch, pacing).
Runs in parallel with GO2 via `asyncio.gather` (wired in REA-18).

## Responsibilities
- Load MediaPipe HandLandmarker + FaceLandmarker once at startup.
- Sample every 5th video frame; aggregate finger-pointing ratio and gaze-shift count → binary flags.
- Analyze WAV audio for inaudible, monotone, and word-by-word pacing → binary flags.
- Return `CVFlags` and `ProsodyFlags` dicts regardless of media quality (no crash on empty/short input).

## Boundaries
- Owns: `app/services/go3/cv_detector.py`, `app/services/go3/prosody_detector.py`, `app/models/cv_detector.py`, `app/models/prosody_detector.py`
- Hands off to: `ResultConsolidator` (REA-24) and `AnalyzeService` orchestrator (REA-18)

## Key Design Decisions
- Uses MediaPipe **Tasks API** (HandLandmarker + FaceLandmarker IMAGE mode) — the legacy
  `mp.solutions` API was removed in mediapipe ≥ 0.10.30.
- `.task` bundles are downloaded once into a gitignored local cache
  (`app/services/go3/models/`) on first `load()` call; subsequent boots are instant.
- `CVDetector` uses singleton pattern (heavy MediaPipe models loaded at startup); `ProsodyAmplitudeDetector` is stateless — instantiated per call like `ScoringEngine`.
- 120s wall-clock timeout on `CVDetector.detect()` guards against long videos on CPU.
- WAV audio < 5s returns all-False prosody flags without crashing.

## Dependencies
- `mediapipe >= 0.10.35` (Tasks API, numpy 2 compatible)
- `librosa >= 0.11.0` (RMS energy, onset detection)
- `praat-parselmouth >= 0.4.7` (F0 pitch extraction)
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
| `ProsodyAmplitudeDetector` | [lld/go3/prosody-detector.md](../lld/go3/prosody-detector.md) |
| `ProsodyDetectorProtocol` | [lld/models/prosody-detector.md](../lld/models/prosody-detector.md) |
| `ProsodyFlags` | [lld/models/prosody-detector.md](../lld/models/prosody-detector.md) |
