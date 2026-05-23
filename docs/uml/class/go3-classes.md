# GO3 Pipeline — Class Diagram

```mermaid
classDiagram
    class CVDetectorProtocol {
        <<Protocol>>
        +detect(video_path: str) CVFlags
    }
    class CVDetector {
        -_hands: Any
        -_face_mesh: Any
        +load() None
        +detect(video_path) CVFlags
        -_finger_in_text_region(image) bool
        -_iris_x(image) float
    }
    class CVFlags {
        <<TypedDict>>
        +finger_pointing: bool
        +loss_of_place: bool
    }
    class ProsodyDetectorProtocol {
        <<Protocol>>
        +detect(wav_path: str) ProsodyFlags
    }
    class ProsodyAmplitudeDetector {
        +detect(wav_path: str) ProsodyFlags
        -_detect_inaudible(y: ndarray) bool
        -_detect_monotone(wav_path: str) bool
        -_detect_word_by_word(y: ndarray, sr) bool
    }
    class ProsodyFlags {
        <<TypedDict>>
        +inaudible_reading: bool
        +monotone_reading: bool
        +word_by_word_reading: bool
    }
    CVDetectorProtocol <|.. CVDetector : implements
    CVDetector --> CVFlags : returns
    ProsodyDetectorProtocol <|.. ProsodyAmplitudeDetector : implements
    ProsodyAmplitudeDetector --> ProsodyFlags : returns
```

## GO3Pipeline

```mermaid
classDiagram
    class GO3Pipeline {
        -_cv_detector: CVDetectorProtocol
        -_prosody_detector: ProsodyDetectorProtocol
        +run(mp4_path: str, wav_path: str) GO3Result
    }
    class GO3Result {
        <<TypedDict>>
        +finger_pointing: bool
        +loss_of_place: bool
        +monotone_reading: bool
        +word_by_word_reading: bool
        +inaudible_reading: bool
    }
    GO3Pipeline --> CVDetectorProtocol : uses
    GO3Pipeline --> ProsodyDetectorProtocol : uses
    GO3Pipeline --> GO3Result : returns
```

## Referenced by
- HLD: `../../hld/go3-pipeline.md`
- LLD: `../../lld/go3/cv-detector.md`
- LLD: `../../lld/models/cv-detector.md`
- LLD: `../../lld/go3/prosody-detector.md`
- LLD: `../../lld/models/prosody-detector.md`
- LLD: `../../lld/go3/go3-pipeline.md`
