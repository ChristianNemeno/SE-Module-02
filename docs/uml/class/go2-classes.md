# GO2 Pipeline — Class Diagram

```mermaid
classDiagram
    class TranscriberProtocol {
        <<Protocol>>
        +transcribe(wav_path: str, passage_text: str) list~WordSegment~
    }
    class WhisperXTranscriber {
        -_model: Any
        -_align_model: Any
        -_metadata: Any
        +load() None
        +transcribe(wav_path, passage_text) list~WordSegment~
    }
    class WordSegment {
        <<TypedDict>>
        +word: str
        +start: float
        +end: float
        +score: float
    }
    class MiscueClassifierProtocol {
        <<Protocol>>
        +classify(transcript_words: list, passage_text: str) MiscueCounts
    }
    class MiscueClassifier {
        +classify(transcript_words, passage_text) MiscueCounts
        -_apply_replace(p_words, t_words, t_scores, tally) None
        -_classify_replace(passage_word, transcript_word, score) MiscueType
        -_detect_repetitions(tokens, scores) tuple
        -_tokenize(text) list~str~
    }
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
    class ScoringEngineProtocol {
        <<Protocol>>
        +score(transcript_words: list, miscue_counts: MiscueCounts, total_passage_words: int) ScoringResult
    }
    class ScoringEngine {
        +score(transcript_words, miscue_counts, total_passage_words) ScoringResult
        -_wpm(words, total_passage_words) float
        -_word_recognition_pct(counts, total) float
        -_reading_level(pct) ReadingLevel
    }
    class ScoringResult {
        <<TypedDict>>
        +wpm: float
        +word_recognition_pct: float
        +reading_level: ReadingLevel
    }
    TranscriberProtocol <|.. WhisperXTranscriber : implements
    WhisperXTranscriber --> WordSegment : returns
    MiscueClassifierProtocol <|.. MiscueClassifier : implements
    MiscueClassifier --> MiscueCounts : returns
    ScoringEngineProtocol <|.. ScoringEngine : implements
    ScoringEngine --> ScoringResult : returns
```

## GO2Pipeline

```mermaid
classDiagram
    class PassageRepositoryProtocol {
        <<Protocol>>
        +fetch(passage_id: str) PassageRecord
    }
    class GO2Pipeline {
        -_transcriber: TranscriberProtocol
        -_classifier: MiscueClassifierProtocol
        -_scorer: ScoringEngineProtocol
        -_passage_repo: PassageRepositoryProtocol
        +run(wav_path: str, passage_id: str) GO2Result
    }
    class GO2Result {
        <<TypedDict>>
        +wpm: float
        +word_recognition_pct: float
        +reading_level: str
        +correct: int
        +mispronunciation: int
        +substitution: int
        +omission: int
        +insertion: int
        +repetition: int
        +refusal_to_pronounce: int
    }
    GO2Pipeline --> TranscriberProtocol : uses
    GO2Pipeline --> MiscueClassifierProtocol : uses
    GO2Pipeline --> ScoringEngineProtocol : uses
    GO2Pipeline --> PassageRepositoryProtocol : uses
    GO2Pipeline --> GO2Result : returns
```

## Referenced by
- HLD: `../../hld/go2-pipeline.md`
- LLD: `../../lld/go2/transcriber.md`
- LLD: `../../lld/go2/miscue-classifier.md`
- LLD: `../../lld/go2/scoring-engine.md`
- LLD: `../../lld/go2/go2-pipeline.md`
- LLD: `../../lld/models/transcription.md`
- LLD: `../../lld/models/miscue.md`
- LLD: `../../lld/models/scoring.md`
