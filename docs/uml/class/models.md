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
        +lip_movement: bool
        +head_movement: bool
        +voice_too_soft: bool
        +loses_place: bool
    }
    class ReadingLevel {
        <<Literal>>
        Frustration
        Instructional
        Independent
    }
    AssessmentResult --> ReadingLevel
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

## Referenced by
- LLD: `../../lld/models/assessment.md`
- LLD: `../../lld/routers/analyze-controller.md`
- LLD: `../../lld/models/transcription.md`
