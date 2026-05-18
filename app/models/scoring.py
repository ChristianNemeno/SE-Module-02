from typing import Protocol, TypedDict

from app.models.assessment import ReadingLevel
from app.models.miscue import MiscueCounts
from app.models.transcription import WordSegment


class ScoringResult(TypedDict):
    """WPM + Phil-IRI scoring fields produced by ScoringEngine."""

    wpm: float
    word_recognition_pct: float
    reading_level: ReadingLevel


class ScoringEngineProtocol(Protocol):
    """Interface for GO2 scoring — pipeline depends on this, not the concrete class."""

    def score(
        self,
        transcript_words: list[WordSegment],
        miscue_counts: MiscueCounts,
        total_passage_words: int,
    ) -> ScoringResult: ...
