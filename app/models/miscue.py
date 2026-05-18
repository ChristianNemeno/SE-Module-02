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


class MiscueClassifierProtocol(Protocol):
    """Interface for Phil-IRI miscue classifiers — pipeline depends on this, not the concrete."""

    def classify(self, transcript_words: list[WordSegment], passage_text: str) -> MiscueCounts: ...
