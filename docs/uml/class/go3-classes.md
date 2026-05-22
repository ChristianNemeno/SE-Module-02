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
    CVDetectorProtocol <|.. CVDetector : implements
    CVDetector --> CVFlags : returns
```

## Referenced by
- HLD: `../../hld/go3-pipeline.md`
- LLD: `../../lld/go3/cv-detector.md`
- LLD: `../../lld/models/cv-detector.md`
