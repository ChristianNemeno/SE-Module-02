# `AnalysisOrchestrator` — Low-Level Design

## Responsibility
Async coordinator: write temp file → extract media → run GO2+GO3 in parallel → merge → persist session.

## Implements
[`AnalysisOrchestrator`](../../uml/class/orchestrator-classes.md)

## Constructor Dependencies
| Parameter | Type | Injected via |
|---|---|---|
| `extractor` | `MediaExtractorProtocol` | `dependencies.py` |
| `go2_pipeline` | `GO2Pipeline` | `dependencies.py` |
| `go3_pipeline` | `GO3Pipeline` | `dependencies.py` |
| `session_repo` | `SessionRepositoryProtocol` | `dependencies.py` |

## Methods
| Method | Purpose | Edge cases |
|---|---|---|
| `run(upload_bytes, source_filename, passage_id, learner_id)` | Public entry point; owns temp dir lifecycle via try/finally | `shutil.rmtree` with `ignore_errors=True` ensures cleanup even on exception |
| `_execute(...)` | Inner pipeline; runs inside the temp dir context | ffmpeg failure → 500; pipeline exception → 500; DB exception → db_save_failed=True; blank learner_id → skip insert |

## Error Handling
| Failure | Behaviour |
|---|---|
| `RuntimeError` from MediaExtractor | `HTTPException(500, {"code": "PIPELINE_FAILED"})` |
| Any exception from `asyncio.gather` | `HTTPException(500, {"code": "PIPELINE_FAILED"})` |
| `ValueError` from ResultConsolidator | `HTTPException(500, {"code": "PIPELINE_FAILED"})` |
| blank `learner_id` | skip DB insert, return result with `db_save_failed=False` |
| Any exception from `session_repo.insert` | return result with `db_save_failed=True` (HTTP 200) |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [orchestrator-classes.md](../../uml/class/orchestrator-classes.md) |
| Sequence flow | [analyze-flow.md](../../uml/sequence/analyze-flow.md) |

## Related
- HLD: [api-layer.md](../../hld/api-layer.md)
- Source: `app/services/analysis_orchestrator.py`
