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

## Current (REA-24 — ResultConsolidator implemented)

```mermaid
flowchart TD
    Client([Client\nAndroid / iOS]) -->|POST /analyze\nX-API-Key| Controller

    subgraph FastAPI["FastAPI (port 8000)"]
        Controller[AnalyzeController\nstub]
        Deps[dependencies.py]
        RC[ResultConsolidator\nmerge + validate]
    end

    subgraph GO2["GO2 Pipeline ✓"]
        T[WhisperXTranscriber]
        C[MiscueClassifier]
        S[ScoringEngine]
    end

    subgraph GO3["GO3 Pipeline ✓"]
        CV[CVDetector]
        PA[ProsodyAmplitudeDetector]
    end

    Deps -->|get_transcriber| T
    Deps -->|get_scoring_engine| S
    Deps -->|get_cv_detector| CV
    Deps -->|get_prosody_detector| PA
    GO2 --> RC
    GO3 --> RC
    RC -->|AssessmentResult| Controller
    Controller -->|stub for now| Client
```

## Current (RR-020 — fully wired)

```mermaid
flowchart TD
    Client([Client\nAndroid / iOS]) -->|POST /analyze\nmultipart/form-data| Controller

    subgraph FastAPI["FastAPI (port 8000)"]
        Controller[AnalyzeController]
        Orchestrator[AnalysisOrchestrator]
        Deps[dependencies.py]
        RC[ResultConsolidator]
    end

    subgraph GO2["GO2 Pipeline"]
        GO2P[GO2Pipeline]
        T[WhisperXTranscriber]
        C[MiscueClassifier]
        S[ScoringEngine]
        PR[PassageRepository]
    end

    subgraph GO3["GO3 Pipeline"]
        GO3P[GO3Pipeline]
        CV[CVDetector]
        PA[ProsodyAmplitudeDetector]
    end

    subgraph DB["Supabase (lfawzhhtqfiwsfonzfbu)"]
        PT[(passages table)]
        ST[(sessions table)]
    end

    Deps -->|injects| Orchestrator
    Controller -->|Depends| Orchestrator
    RC -->|AssessmentResult| Orchestrator

    Orchestrator -->|asyncio.to_thread| ME[MediaExtractor\nffmpeg]
    Orchestrator -->|asyncio.gather| GO2P
    Orchestrator -->|asyncio.gather| GO3P

    GO2P --> T & C & S
    GO2P --> PR --> PT
    GO3P --> CV & PA

    GO2P -.->|results| RC
    GO3P -.->|results| RC

    Orchestrator -->|asyncio.to_thread| SR[SessionRepository]
    SR --> ST
    Orchestrator -->|AssessmentResult| Controller
    Controller --> Client
```

## Referenced by
- HLD: `../../hld/system-overview.md`
