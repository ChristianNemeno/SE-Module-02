# Orchestrator — Class Diagram

## AnalysisOrchestrator

```mermaid
classDiagram
    class MediaExtractorProtocol {
        <<Protocol>>
        +extract(source_path: str, out_dir: str) ExtractionResult
    }
    class MediaExtractor {
        +extract(source_path: str, out_dir: str) ExtractionResult
    }
    class DebugSaverProtocol {
        <<Protocol>>
        +save(wav_path: str, result: AssessmentResult, passage_id: str, learner_id: str) None
    }
    class AudioDebugSaver {
        -_debug_dir: str
        +save(wav_path, result, passage_id, learner_id) None
    }
    class NullDebugSaver {
        +save(wav_path, result, passage_id, learner_id) None
    }
    class PassageRepository {
        -_client: Client
        +fetch(passage_id: str) PassageRecord
    }
    class SessionRepository {
        -_client: Client
        +insert(record: SessionRecord) None
    }
    class AnalysisOrchestrator {
        -_extractor: MediaExtractorProtocol
        -_go2: GO2Pipeline
        -_go3: GO3Pipeline
        -_session_repo: SessionRepositoryProtocol
        -_debug_saver: DebugSaverProtocol
        +run(upload_bytes, source_filename, passage_id, learner_id) AssessmentResult
        -_execute(upload_bytes, source_filename, passage_id, learner_id, temp_dir) AssessmentResult
    }
    MediaExtractorProtocol <|.. MediaExtractor : implements
    DebugSaverProtocol <|.. AudioDebugSaver : implements
    DebugSaverProtocol <|.. NullDebugSaver : implements
    AnalysisOrchestrator --> MediaExtractorProtocol : uses
    AnalysisOrchestrator --> GO2Pipeline : uses
    AnalysisOrchestrator --> GO3Pipeline : uses
    AnalysisOrchestrator --> SessionRepositoryProtocol : uses
    AnalysisOrchestrator --> DebugSaverProtocol : uses
    SessionRepositoryProtocol <|.. SessionRepository : implements
    PassageRepositoryProtocol <|.. PassageRepository : implements
    GO2Pipeline --> PassageRepositoryProtocol : uses
    AnalysisOrchestrator --> AssessmentResult : returns
```

## Referenced by
- HLD: `../../hld/api-layer.md`
- LLD: `../../lld/services/analysis-orchestrator.md`
- LLD: `../../lld/services/debug-audio-saver.md`
- LLD: `../../lld/models/debug-saver.md`
- LLD: `../../lld/services/media-extractor.md`
- LLD: `../../lld/repositories/session-repository.md`
- LLD: `../../lld/repositories/passage-repository.md`
