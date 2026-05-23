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
        +run(upload_bytes, source_filename, passage_id, learner_id) AssessmentResult
        -_execute(upload_bytes, source_filename, passage_id, learner_id, temp_dir) AssessmentResult
    }
    MediaExtractorProtocol <|.. MediaExtractor : implements
    AnalysisOrchestrator --> MediaExtractorProtocol : uses
    AnalysisOrchestrator --> GO2Pipeline : uses
    AnalysisOrchestrator --> GO3Pipeline : uses
    AnalysisOrchestrator --> SessionRepositoryProtocol : uses
    SessionRepositoryProtocol <|.. SessionRepository : implements
    PassageRepositoryProtocol <|.. PassageRepository : implements
    GO2Pipeline --> PassageRepositoryProtocol : uses
    AnalysisOrchestrator --> AssessmentResult : returns
```

## Referenced by
- HLD: `../../hld/api-layer.md`
- LLD: `../../lld/services/analysis-orchestrator.md`
- LLD: `../../lld/services/media-extractor.md`
- LLD: `../../lld/repositories/session-repository.md`
- LLD: `../../lld/repositories/passage-repository.md`
