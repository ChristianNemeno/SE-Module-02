# `DebugSaverProtocol` / `NullDebugSaver` — Low-Level Design

## Responsibility
`DebugSaverProtocol` — narrow interface for persisting WAV + result JSON after a completed analysis.
`NullDebugSaver` — no-op implementation (null-object pattern) used when `DEBUG_AUDIO_DIR` is unset.

## Implements
Both live in `app/models/debug_saver.py`. `NullDebugSaver` satisfies `DebugSaverProtocol` structurally.

## Methods
| Method | Purpose | Edge cases |
|---|---|---|
| `save(wav_path, result, passage_id, learner_id)` | Persist debug artifacts for one analysis run | `NullDebugSaver` — does nothing; `AudioDebugSaver` — copies WAV + writes JSON |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [orchestrator-classes.md](../../uml/class/orchestrator-classes.md) |

## Related
- HLD: [api-layer.md](../../hld/api-layer.md)
- Source: `app/models/debug_saver.py`
