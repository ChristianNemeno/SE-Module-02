# `MediaExtractor` — Low-Level Design

## Responsibility
Extracts a 16 kHz mono WAV and a normalised MP4 from an uploaded video file using the system ffmpeg binary.

## Implements
[`MediaExtractorProtocol`](../../uml/class/orchestrator-classes.md)

## Constructor Dependencies
None — stateless, instantiated per-request.

## Methods
| Method | Purpose | Edge cases |
|---|---|---|
| `extract(source_path, out_dir)` | Runs two ffmpeg subprocesses → writes `audio.wav` + `video.mp4` → returns `ExtractionResult` | `CalledProcessError` → `RuntimeError("FFmpeg failed: ...")` propagated to orchestrator |

## Subprocess Commands
| Output | Command flags |
|---|---|
| `audio.wav` | `-ac 1 -ar 16000 -sample_fmt s16` |
| `video.mp4` | `-c:v libx264 -preset fast -crf 23 -an` |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [orchestrator-classes.md](../../uml/class/orchestrator-classes.md) |
| Sequence flow | [analyze-flow.md](../../uml/sequence/analyze-flow.md) |

## Related
- HLD: [api-layer.md](../../hld/api-layer.md)
- Source: `app/services/media_extractor.py`
