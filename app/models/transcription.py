from typing import Protocol, TypedDict


class WordSegment(TypedDict):
    """Word-level output shape from WhisperX forced alignment."""

    word: str
    start: float
    end: float
    score: float


class TranscriberProtocol(Protocol):
    """Interface for ASR transcribers — pipeline depends on this, not the concrete class."""

    def transcribe(self, wav_path: str, passage_text: str) -> list[WordSegment]: ...
