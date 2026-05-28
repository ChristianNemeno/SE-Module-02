from typing import TypedDict


class GO2Result(TypedDict):
    """Flat scoring + miscue output from the GO2 audio pipeline."""

    wpm: float
    word_recognition_pct: float
    reading_level: str
    correct: int
    mispronunciation: int
    substitution: int
    omission: int
    insertion: int
    repetition: int


class GO3Result(TypedDict):
    """Behavioral flags from the GO3 video + prosody pipeline."""

    finger_pointing: bool
    loss_of_place: bool
    monotone_reading: bool
    word_by_word_reading: bool
    inaudible_reading: bool
