from typing import Literal, Protocol, TypedDict

from app.models.transcription import WordSegment

type MiscueType = Literal[
    "correct",
    "mispronunciation",
    "substitution",
    "omission",
    "insertion",
    "repetition",
    "refusal_to_pronounce",
]


class MiscueCounts(TypedDict):
    """Per-category miscue counts produced by GO2 classification."""

    correct: int
    mispronunciation: int
    substitution: int
    omission: int
    insertion: int
    repetition: int
    refusal_to_pronounce: int


class MiscueDetail(TypedDict):
    """One aligned word decision — its category plus the words/timing involved."""

    miscue_type: MiscueType
    passage_word: str | None  # None for insertion / repetition
    transcript_word: str | None  # None for omission
    start: float | None  # spoken-word start secs; None when no transcript word
    end: float | None  # spoken-word end secs; None when no transcript word


class MiscueClassifierProtocol(Protocol):
    """Interface for Phil-IRI miscue classifiers — pipeline depends on this, not the concrete."""

    def classify(
        self,
        transcript_words: list[WordSegment],
        passage_text: str,
        proper_nouns: list[str] | None = None,
    ) -> MiscueCounts: ...

    def detail(
        self,
        transcript_words: list[WordSegment],
        passage_text: str,
        proper_nouns: list[str] | None = None,
    ) -> list[MiscueDetail]: ...


class MiscueReporterProtocol(Protocol):
    """Interface for miscue reporters — pipeline depends on this, not the concrete."""

    def report(self, passage_id: str, details: list[MiscueDetail]) -> None: ...
