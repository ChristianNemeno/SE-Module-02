from app.models.cv_detector import CVDetectorProtocol
from app.models.pipeline_results import GO3Result
from app.models.prosody_detector import ProsodyDetectorProtocol


class GO3Pipeline:
    """Sequences the GO3 video + prosody pipeline: CV detection + prosody analysis."""

    def __init__(
        self,
        cv_detector: CVDetectorProtocol,
        prosody_detector: ProsodyDetectorProtocol,
    ) -> None:
        """Inject CV and prosody detectors."""
        self._cv_detector = cv_detector
        self._prosody_detector = prosody_detector

    def run(self, mp4_path: str, wav_path: str) -> GO3Result:
        """Run CV detection on video and prosody analysis on audio, return merged flags."""
        cv_flags = self._cv_detector.detect(mp4_path)
        prosody_flags = self._prosody_detector.detect(wav_path)
        return GO3Result(
            finger_pointing=cv_flags["finger_pointing"],
            loss_of_place=cv_flags["loss_of_place"],
            monotone_reading=prosody_flags["monotone_reading"],
            word_by_word_reading=prosody_flags["word_by_word_reading"],
            inaudible_reading=prosody_flags["inaudible_reading"],
        )
