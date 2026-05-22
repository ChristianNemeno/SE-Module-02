# System Architecture — Component Diagram

## Current (RR-021 — WhisperX wired at startup)

```mermaid
flowchart TD
    Client([Client\nAndroid / iOS]) -->|POST /analyze\nX-API-Key| Controller

    subgraph FastAPI["FastAPI (port 8000)"]
        Controller[AnalyzeController]
        Config[Settings\npydantic-settings]
        Deps[dependencies.py]
    end

    subgraph GO2["GO2 Pipeline (partial)"]
        T[WhisperXTranscriber\nloaded at startup]
    end

    Controller -->|reads| Config
    Deps -->|get_transcriber| T
    Controller -->|returns stub| Client
```

## Current (REA-22 — GO3 CVDetector wired)

```mermaid
flowchart TD
    Client([Client\nAndroid / iOS]) -->|POST /analyze\nX-API-Key| Controller

    subgraph FastAPI["FastAPI (port 8000)"]
        Controller[AnalyzeController\nstub]
        Deps[dependencies.py]
    end

    subgraph GO2["GO2 Pipeline ✓"]
        T[WhisperXTranscriber]
        C[MiscueClassifier]
        S[ScoringEngine]
    end

    subgraph GO3["GO3 Pipeline (partial)"]
        CV[CVDetector\nloaded at startup]
    end

    Deps -->|get_transcriber| T
    Deps -->|get_scoring_engine| S
    Deps -->|get_cv_detector| CV
    Controller -->|returns stub| Client
```

## Target (RR-020 — after full wiring)

```mermaid
flowchart TD
    Client([Client\nAndroid / iOS]) -->|POST /analyze\nmultipart/form-data| Controller

    subgraph FastAPI["FastAPI (port 8000)"]
        Controller[AnalyzeController]
        Service[AnalyzeService]
        Deps[dependencies.py]
    end

    subgraph GO2["GO2 Pipeline"]
        T[WhisperXTranscriber]
        C[MiscueClassifier]
        S[ScoringEngine]
    end

    subgraph GO3["GO3 Pipeline"]
        CV[CVDetector]
        PA[ProsodyAmplitudeDetector]
    end

    Deps -->|injects| Service
    Controller --> Service
    Service --> GO2Pipeline
    GO2Pipeline --> T
    GO2Pipeline --> C
    GO2Pipeline --> S
    Service --> GO3Pipeline
    GO3Pipeline --> CV
    GO3Pipeline --> PA
    Service --> Repo[SupabaseSessionRepository]
    Repo --> DB[(Supabase\nsessions table)]
    Service --> Controller
    Controller --> Client
```

## Referenced by
- HLD: `../../hld/system-overview.md`
