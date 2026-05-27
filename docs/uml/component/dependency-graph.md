# Dependency Wiring — Component Graph

```mermaid
flowchart LR
    deps[dependencies.py]

    deps -->|singleton| T[WhisperXTranscriber]
    deps -->|per-call| C[MiscueClassifier]
    deps -->|per-call| S[ScoringEngine]
    deps -->|singleton| CV[CVDetector]
    deps -->|per-call| PA[ProsodyAmplitudeDetector]
    deps -->|per-call| ME[MediaExtractor]
    deps -->|per-call| PR[PassageRepository\nclient]
    deps -->|per-call| SR[SessionRepository\nclient]
    deps -->|per-call| RPT[MiscueReporter]
    deps -->|per-call| PNE[CapitalizationProperNounExtractor]
    deps -->|per-call\nDEBUG_AUDIO_DIR set| DS[AudioDebugSaver]
    deps -->|per-call\nDEBUG_AUDIO_DIR unset| NDS[NullDebugSaver]

    deps -->|constructs| GO2[GO2Pipeline\nT + C + S + PR + RPT + PNE]
    deps -->|constructs| GO3[GO3Pipeline\nCV + PA]
    deps -->|constructs| ORC[AnalysisOrchestrator\nME + GO2 + GO3 + SR + DS/NDS]

    ORC -->|Depends| Ctrl[AnalyzeController\nPOST /analyze]
```

## Referenced by
- HLD: `../../hld/go2-pipeline.md`
- HLD: `../../hld/go3-pipeline.md`
- HLD: `../../hld/api-layer.md`
