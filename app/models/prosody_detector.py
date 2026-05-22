# app/models/prosody_detector.py
from typing import Protocol, TypedDict


class ProsodyFlags(TypedDict):
    """GO3 behavioral flags from WAV audio — inaudible, monotone, word-by-word pacing."""

    inaudible_reading: bool
    monotone_reading: bool
    word_by_word_reading: bool


class ProsodyDetectorProtocol(Protocol):
    """Interface for prosody detectors — pipeline depends on this, not the concrete class."""

    def detect(self, wav_path: str) -> ProsodyFlags: ...
