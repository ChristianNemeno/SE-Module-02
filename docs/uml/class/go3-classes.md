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

## Referenced by
- HLD: `../../hld/go3-pipeline.md`
- LLD: `../../lld/go3/cv-detector.md`
- LLD: `../../lld/models/cv-detector.md`
- LLD: `../../lld/go3/prosody-detector.md`
- LLD: `../../lld/models/prosody-detector.md`
