# `AudioDebugSaver` — Low-Level Design

## Responsibility
Copies the extracted WAV + writes a companion JSON result file to a persistent debug directory after each successful analysis.

## Implements
[`DebugSaverProtocol`](../../uml/class/orchestrator-classes.md)

## Constructor Dependencies
| Parameter | Type | Injected via |
|---|---|---|
| `debug_dir` | `str` | `dependencies.py` (from `Settings.DEBUG_AUDIO_DIR`) |

## Methods
| Method | Purpose | Edge cases |
|---|---|---|
| `save(wav_path, result, passage_id, learner_id)` | Copies WAV + writes `{timestamp}_{passage_id}_{learner_id}.json` | `makedirs(exist_ok=True)` called in `__init__`; caller wraps in try/except — non-fatal; `_safe()` strips path-traversal chars from identifiers; realpath boundary check raises `ValueError` if traversal detected |

## Security
- `_safe()` restricts `passage_id` / `learner_id` to `[A-Za-z0-9_.-]`, max 64 chars — prevents path traversal via user-controlled request fields.
- `__init__` resolves `debug_dir` via `os.path.realpath()` — symlink-safe boundary.
- `save()` re-checks resolved destination starts within `debug_dir + os.sep` — belt-and-suspenders.

## Output Format
Files land in `DEBUG_AUDIO_DIR/`:
```
20260527_143201_passage-01_student42.wav
20260527_143201_passage-01_student42.json
```
JSON is `AssessmentResult.model_dump()` — all fields, indent=2.

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [orchestrator-classes.md](../../uml/class/orchestrator-classes.md) |
| Dependency wiring | [dependency-graph.md](../../uml/component/dependency-graph.md) |

## Related
- HLD: [api-layer.md](../../hld/api-layer.md)
- Source: `app/services/debug_audio_saver.py`
