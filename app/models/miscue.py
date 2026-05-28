from typing import Literal, Protocol, TypedDict

from app.models.transcription import WordSegment

type MiscueType = Literal[
    "correct",
    "mispronunciation",
    "substitution",
    "omission",
    "insertion",
    "repetition",
]


class MiscueCounts(TypedDict):
    """Per-category miscue counts produced by GO2 classification."""

    correct: int
    mispronunciation: int
    substitution: int
    omission: int
    insertion: int
    repetition: int


class MiscueDetail(TypedDict):
    """One aligned event — a single word or a contiguous phrase, per Phil-IRI counting rules."""

    miscue_type: MiscueType
    passage_word: str | None  # None for insertion; may be a multi-word phrase for omission/substitution
    transcript_word: str | None  # None for omission; may be a multi-word phrase for insertion/repetition/substitution
    start: float | None  # spoken span start secs; None when no transcript counterpart
    end: float | None  # spoken span end secs; None when no transcript counterpart


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
