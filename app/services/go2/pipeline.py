from app.models.miscue import MiscueClassifierProtocol
from app.models.passage import PassageRepositoryProtocol
from app.models.pipeline_results import GO2Result
from app.models.scoring import ScoringEngineProtocol
from app.models.transcription import TranscriberProtocol


class GO2Pipeline:
    """Sequences the full GO2 audio pipeline: passage fetch → ASR → miscue → scoring."""

    def __init__(
        self,
        transcriber: TranscriberProtocol,
        classifier: MiscueClassifierProtocol,
        scorer: ScoringEngineProtocol,
        passage_repo: PassageRepositoryProtocol,
    ) -> None:
        """Inject all GO2 pipeline dependencies."""
        self._transcriber = transcriber
        self._classifier = classifier
        self._scorer = scorer
        self._passage_repo = passage_repo

    def run(self, wav_path: str, passage_id: str) -> GO2Result:
        """Run the full GO2 pipeline. Raises ValueError if passage_id is unknown."""
        passage = self._passage_repo.fetch(passage_id)
        words = self._transcriber.transcribe(wav_path, passage["text"])
        miscues = self._classifier.classify(words, passage["text"])
        scoring = self._scorer.score(words, miscues, passage["word_count"])
        return GO2Result(
            wpm=scoring["wpm"],
            word_recognition_pct=scoring["word_recognition_pct"],
            reading_level=scoring["reading_level"],
            correct=miscues["correct"],
            mispronunciation=miscues["mispronunciation"],
            substitution=miscues["substitution"],
            omission=miscues["omission"],
            insertion=miscues["insertion"],
            repetition=miscues["repetition"],
            refusal_to_pronounce=miscues["refusal_to_pronounce"],
        )
