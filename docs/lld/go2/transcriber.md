# `WhisperXTranscriber` — Low-Level Design

## Responsibility
Holds pre-loaded WhisperX model references and converts a WAV file into a typed list of word-level timestamps via forced alignment.

## Implements
[`TranscriberProtocol`](../../uml/class/go2-classes.md)

## Constructor Dependencies
None — models are loaded into instance attributes via `load()`, called once from `load_models()` at startup.

## Methods
| Method | Purpose | Edge cases |
|---|---|---|
| `load()` | Loads WhisperX base model + alignment model into instance attrs | Calling again overwrites existing models |
| `transcribe(wav_path, passage_text)` | Runs ASR + forced alignment, returns `list[WordSegment]` | Returns `[]` for silence-only audio (no `word_segments` in output) |

## Module-Level Functions
| Function | Purpose |
|---|---|
| `load_models()` | Creates singleton `WhisperXTranscriber` and calls `.load()`; stored as `_transcriber` |
| `get_transcriber_instance()` | Returns the singleton; raises `RuntimeError` if called before startup |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [go2-classes.md](../../uml/class/go2-classes.md) |
| Pipeline flow | [go2-pipeline-flow.md](../../uml/sequence/go2-pipeline-flow.md) |

## Related
- HLD: [go2-pipeline.md](../../hld/go2-pipeline.md)
- Source: `app/services/go2/transcriber.py`
