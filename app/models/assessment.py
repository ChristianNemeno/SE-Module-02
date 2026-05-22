from typing import Literal

from pydantic import BaseModel, Field

type ReadingLevel = Literal["Frustration", "Instructional", "Independent"]


class AssessmentResult(BaseModel):
    """Fully typed result from GO2 + GO3 pipeline. Schema returned by /analyze."""

    # GO2 — audio scoring
    wpm: float
    word_recognition_pct: float = Field(ge=0, le=100)
    reading_level: ReadingLevel
    correct: int
    mispronunciation: int
    substitution: int
    omission: int
    insertion: int
    repetition: int
    refusal_to_pronounce: int

    # GO3 — behavioral flags
    finger_pointing: bool
    loss_of_place: bool
    monotone_reading: bool
    word_by_word_reading: bool
    inaudible_reading: bool
