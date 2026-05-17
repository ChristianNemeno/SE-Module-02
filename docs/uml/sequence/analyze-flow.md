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

## Full Flow (RR-020 — to be updated)

```mermaid
sequenceDiagram
    participant Client
    participant AnalyzeController
    participant AnalyzeService
    participant GO2Pipeline
    participant GO3Pipeline
    participant Supabase

    Client->>AnalyzeController: POST /analyze (file, passage_id, X-API-Key)
    AnalyzeController->>AnalyzeController: _check_api_key()
    AnalyzeController->>AnalyzeService: run(file, passage_id)
    AnalyzeService->>AnalyzeService: extract_audio() / normalize_video()
    par asyncio.gather
        AnalyzeService->>GO2Pipeline: run(wav_path, passage_id)
        GO2Pipeline-->>AnalyzeService: GO2Result
    and
        AnalyzeService->>GO3Pipeline: run(mp4_path, wav_path)
        GO3Pipeline-->>AnalyzeService: GO3Result
    end
    AnalyzeService->>Supabase: sessions.insert(result)
    AnalyzeService-->>AnalyzeController: AssessmentResult
    AnalyzeController-->>Client: 200 AssessmentResult
```

## Referenced by
- HLD: `../../hld/api-layer.md`
- HLD: `../../hld/system-overview.md`
- LLD: `../../lld/routers/analyze-controller.md`
