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
    TranscriberProtocol <|.. WhisperXTranscriber : implements
    WhisperXTranscriber --> WordSegment : returns
    MiscueClassifierProtocol <|.. MiscueClassifier : implements
    MiscueClassifier --> MiscueCounts : returns
```

## Referenced by
- HLD: `../../hld/go2-pipeline.md`
- LLD: `../../lld/go2/transcriber.md`
- LLD: `../../lld/go2/miscue-classifier.md`
- LLD: `../../lld/models/transcription.md`
- LLD: `../../lld/models/miscue.md`
