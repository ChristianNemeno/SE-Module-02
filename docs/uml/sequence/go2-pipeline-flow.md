# GO2 Pipeline — Sequence Diagram

## Transcription Flow (RR-021)

```mermaid
sequenceDiagram
    participant AnalyzeService
    participant WhisperXTranscriber
    participant whisperx

    AnalyzeService->>WhisperXTranscriber: transcribe(wav_path, passage_text)
    WhisperXTranscriber->>whisperx: model.transcribe(wav_path, batch_size=4)
    whisperx-->>WhisperXTranscriber: {segments: [...]}
    WhisperXTranscriber->>whisperx: align(segments, align_model, metadata, wav_path)
    whisperx-->>WhisperXTranscriber: {word_segments: [{word, start, end, score}]}
    WhisperXTranscriber-->>AnalyzeService: list[WordSegment]
```

## Full GO2 Flow (RR-022 + RR-023 — to be updated)

```mermaid
sequenceDiagram
    participant AnalyzeService
    participant GO2Pipeline
    participant PassageRepository
    participant CapitalizationProperNounExtractor
    participant WhisperXTranscriber
    participant MiscueClassifier
    participant MiscueReporter
    participant ScoringEngine

    AnalyzeService->>GO2Pipeline: run(wav_path, passage_id)
    GO2Pipeline->>PassageRepository: fetch(passage_id)
    PassageRepository-->>GO2Pipeline: PassageRecord (text, word_count, proper_nouns)
    GO2Pipeline->>CapitalizationProperNounExtractor: extract(passage_text)
    CapitalizationProperNounExtractor-->>GO2Pipeline: list[str] (merged with PassageRecord.proper_nouns)
    GO2Pipeline->>WhisperXTranscriber: transcribe(wav_path, passage_text)
    WhisperXTranscriber-->>GO2Pipeline: list[WordSegment]
    GO2Pipeline->>MiscueClassifier: classify(words, passage_text, proper_nouns)
    MiscueClassifier-->>GO2Pipeline: MiscueCounts
    GO2Pipeline->>MiscueClassifier: detail(words, passage_text, proper_nouns)
    MiscueClassifier-->>GO2Pipeline: list[MiscueDetail]
    GO2Pipeline->>MiscueReporter: report(passage_id, details)
    MiscueReporter-->>GO2Pipeline: prints to console
    GO2Pipeline->>ScoringEngine: score(words, counts, word_count)
    ScoringEngine-->>GO2Pipeline: GO2Result
    GO2Pipeline-->>AnalyzeService: GO2Result
```

## Referenced by
- HLD: `../../hld/go2-pipeline.md`
- LLD: `../../lld/go2/transcriber.md`
