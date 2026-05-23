# POST /analyze — Sequence Diagram

## Stub Flow (RR-004)

```mermaid
sequenceDiagram
    participant Client
    participant AnalyzeController
    participant Settings

    Client->>AnalyzeController: POST /analyze (file, passage_id, X-API-Key)
    AnalyzeController->>Settings: get_settings().API_KEY
    alt invalid key
        AnalyzeController-->>Client: 401 Invalid API key
    else valid key
        AnalyzeController-->>Client: 200 AssessmentResult (stub)
    end
```

## Full Flow (RR-020 — implemented)

```mermaid
sequenceDiagram
    participant Client
    participant AnalyzeController
    participant AnalysisOrchestrator
    participant MediaExtractor
    participant GO2Pipeline
    participant GO3Pipeline
    participant ResultConsolidator
    participant SessionRepository

    Client->>AnalyzeController: POST /analyze (file, passage_id, learner_id, X-API-Key)
    AnalyzeController->>AnalyzeController: _check_api_key()
    alt invalid key
        AnalyzeController-->>Client: 401 Invalid API key
    end
    AnalyzeController->>AnalysisOrchestrator: run(bytes, filename, passage_id, learner_id)
    AnalysisOrchestrator->>AnalysisOrchestrator: mkdtemp() + write upload bytes
    AnalysisOrchestrator->>MediaExtractor: extract(source_path, temp_dir)
    alt ffmpeg fails
        MediaExtractor-->>AnalysisOrchestrator: RuntimeError
        AnalysisOrchestrator-->>Client: 500 PIPELINE_FAILED
    end
    MediaExtractor-->>AnalysisOrchestrator: ExtractionResult(wav_path, mp4_path)
    par asyncio.gather
        AnalysisOrchestrator->>GO2Pipeline: run(wav_path, passage_id)
        GO2Pipeline-->>AnalysisOrchestrator: GO2Result
    and
        AnalysisOrchestrator->>GO3Pipeline: run(mp4_path, wav_path)
        GO3Pipeline-->>AnalysisOrchestrator: GO3Result
    end
    AnalysisOrchestrator->>ResultConsolidator: merge(go2_result, go3_result)
    ResultConsolidator-->>AnalysisOrchestrator: AssessmentResult
    alt learner_id blank
        AnalysisOrchestrator-->>Client: 200 AssessmentResult (no DB write)
    end
    AnalysisOrchestrator->>SessionRepository: insert(SessionRecord)
    alt DB insert fails
        SessionRepository-->>AnalysisOrchestrator: Exception
        AnalysisOrchestrator-->>Client: 200 AssessmentResult (db_save_failed=True)
    end
    AnalysisOrchestrator-->>AnalyzeController: AssessmentResult
    AnalyzeController-->>Client: 200 AssessmentResult
```

## Referenced by
- HLD: `../../hld/api-layer.md`
- HLD: `../../hld/system-overview.md`
- LLD: `../../lld/routers/analyze-controller.md`
- LLD: `../../lld/services/analysis-orchestrator.md`
