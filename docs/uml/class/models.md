# Models — Class Diagram

## AssessmentResult

```mermaid
classDiagram
    class AssessmentResult {
        <<Pydantic Model>>
        +wpm: float
        +word_recognition_pct: float
        +reading_level: ReadingLevel
        +correct: int
        +mispronunciation: int
        +substitution: int
        +omission: int
        +insertion: int
        +repetition: int
        +refusal_to_pronounce: int
        +finger_pointing: bool
        +loss_of_place: bool
        +monotone_reading: bool
        +word_by_word_reading: bool
        +inaudible_reading: bool
    }
    class ReadingLevel {
        <<Literal>>
        Frustration
        Instructional
        Independent
    }
    AssessmentResult --> ReadingLevel
```

## ResultConsolidator

```mermaid
classDiagram
    class ResultConsolidator {
        +merge(go2_result: dict, go3_result: dict)$ AssessmentResult
    }
    ResultConsolidator --> AssessmentResult : produces
```

## WordSegment

```mermaid
classDiagram
    class WordSegment {
        <<TypedDict>>
        +word: str
        +start: float
        +end: float
        +score: float
    }
```

## MiscueCounts

```mermaid
classDiagram
    class MiscueCounts {
        <<TypedDict>>
        +correct: int
        +mispronunciation: int
        +substitution: int
        +omission: int
        +insertion: int
        +repetition: int
        +refusal_to_pronounce: int
    }
    class MiscueClassifierProtocol {
        <<Protocol>>
        +classify(transcript_words: list, passage_text: str) MiscueCounts
    }
    MiscueClassifierProtocol --> MiscueCounts : returns
```

## ScoringResult

```mermaid
classDiagram
    class ScoringResult {
        <<TypedDict>>
        +wpm: float
        +word_recognition_pct: float
        +reading_level: ReadingLevel
    }
    class ScoringEngineProtocol {
        <<Protocol>>
        +score(transcript_words: list, miscue_counts: MiscueCounts, total_passage_words: int) ScoringResult
    }
    ScoringEngineProtocol --> ScoringResult : returns
```

## Referenced by
- LLD: `../../lld/models/assessment.md`
- LLD: `../../lld/utils/result-consolidator.md`
- LLD: `../../lld/routers/analyze-controller.md`
- LLD: `../../lld/models/transcription.md`
- LLD: `../../lld/models/miscue.md`
- LLD: `../../lld/models/scoring.md`
