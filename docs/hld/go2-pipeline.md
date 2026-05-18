# GO2 Pipeline — High-Level Design

## Purpose
The GO2 pipeline processes a student's reading audio recording to produce ASR-based metrics: words-per-minute, word recognition %, Phil-IRI reading level, and miscue counts. It runs from a WAV file and a reference passage text.

## Responsibilities
- Transcribe audio to word-level timestamps via WhisperX forced alignment
- Classify each word against Phil-IRI's 7 miscue categories
- Compute WPM, word recognition %, and reading level from transcript + miscue data

## Boundaries
- Owns: transcription, miscue classification, scoring
- Hands off to: `AnalyzeService` (RR-020) which calls GO2 and GO3 in parallel, then consolidates results

## Key Design Decisions
- WhisperX models loaded once at startup via `lifespan` — not per request — to meet the 90s SLA
- `TranscriberProtocol` decouples the pipeline from WhisperX; any ASR backend can be swapped in
- All whisperx calls isolated in `transcriber.py` with `# type: ignore` — typed boundary at `list[WordSegment]`
- CPU device for pilot; swap to `"cuda"` in one place once driver is stable
- `ScoringEngine` is stateless and instantiated per request — no models to preload, cheap to construct
- Reading-level thresholds use `>=` so boundary ties (exactly 97% / 91%) resolve to the higher classification; error set excludes `insertion` and `repetition` per Phil-IRI

## Dependencies
- `whisperx` — ASR + forced alignment (no type stubs)
- `torch` (CPU for pilot, CUDA-swappable)

## Diagrams
| Diagram | Link |
|---|---|
| Component / architecture | [system-architecture.md](../uml/component/system-architecture.md) |
| Class relationships | [go2-classes.md](../uml/class/go2-classes.md) |
| Pipeline flow | [go2-pipeline-flow.md](../uml/sequence/go2-pipeline-flow.md) |

## Classes in this Domain
| Class | LLD |
|---|---|
| `WhisperXTranscriber` | [lld/go2/transcriber.md](../lld/go2/transcriber.md) |
| `MiscueClassifier` | [lld/go2/miscue-classifier.md](../lld/go2/miscue-classifier.md) |
| `ScoringEngine` | [lld/go2/scoring-engine.md](../lld/go2/scoring-engine.md) |
