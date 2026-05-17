from typing import Literal

from pydantic import BaseModel, Field

type ReadingLevel = Literal["Frustration", "Instructional", "Independent"]


class AssessmentResult(BaseModel):
    """Fully typed result sa GO2 + GO3 pipeline. Mao ni ang schema nga gi-return sa /analyze."""

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
    lip_movement: bool
    head_movement: bool
    voice_too_soft: bool
    loses_place: bool
