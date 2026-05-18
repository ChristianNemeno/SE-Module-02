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
    participant WhisperXTranscriber
    participant MiscueClassifier
    participant ScoringEngine

    AnalyzeService->>GO2Pipeline: run(wav_path, passage_text)
    GO2Pipeline->>WhisperXTranscriber: transcribe(wav_path, passage_text)
    WhisperXTranscriber-->>GO2Pipeline: list[WordSegment]
    GO2Pipeline->>MiscueClassifier: classify(words, passage_text)
    MiscueClassifier-->>GO2Pipeline: MiscueCounts
    GO2Pipeline->>ScoringEngine: score(words, counts)
    ScoringEngine-->>GO2Pipeline: GO2Result
    GO2Pipeline-->>AnalyzeService: GO2Result
```

## Referenced by
- HLD: `../../hld/go2-pipeline.md`
- LLD: `../../lld/go2/transcriber.md`
