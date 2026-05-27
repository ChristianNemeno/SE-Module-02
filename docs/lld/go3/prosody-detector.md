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
| `_detect_monotone(wav_path)` | F0 std-dev < 30 Hz → `monotone_reading: True` | < 10 voiced frames → False |
| `_detect_word_by_word(y, sr)` | silence_ratio ≥ 0.40 AND speech_rate < 1.0 seg/s → `word_by_word_reading: True` | Empty audio → False |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [go3-classes.md](../../uml/class/go3-classes.md) |

## Related
- HLD: [go3-pipeline.md](../../hld/go3-pipeline.md)
- Source: `app/services/go3/prosody_detector.py`
