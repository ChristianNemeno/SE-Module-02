# `ProsodyAmplitudeDetector` — Low-Level Design

## Responsibility
Extracts three prosody-based behavioral flags from a WAV file using librosa (RMS + onsets) and parselmouth (F0 pitch).

## Implements
[`ProsodyDetectorProtocol`](../../uml/class/go3-classes.md)

## Constructor Dependencies
None — stateless, instantiated per request via `dependencies.py`.

## Methods
| Method | Purpose | Edge cases |
|---|---|---|
| `detect(wav_path)` | Loads WAV once, runs all three checks, returns `ProsodyFlags` | Audio < 5s → all-False immediately |
| `_detect_inaudible(y)` | Mean RMS < threshold → `inaudible_reading: True` | Silent WAV returns True |
| `_detect_monotone(wav_path)` | F0 std-dev < 20 Hz → `monotone_reading: True` | < 10 voiced frames → False |
| `_detect_word_by_word(y, sr)` | Mean IOI > 0.8s → `word_by_word_reading: True` | < 3 onset events → False |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [go3-classes.md](../../uml/class/go3-classes.md) |

## Related
- HLD: [go3-pipeline.md](../../hld/go3-pipeline.md)
- Source: `app/services/go3/prosody_detector.py`
