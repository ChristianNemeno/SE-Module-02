from typing import Protocol, TypedDict


class WordSegment(TypedDict):
    """Word-level output shape gikan sa WhisperX forced alignment."""

    word: str
    start: float
    end: float
    score: float


class TranscriberProtocol(Protocol):
    """Protocol interface para sa ASR transcribers — ang GO2 pipeline depende diri, dili sa concrete class."""

    def transcribe(self, wav_path: str, passage_text: str) -> list[WordSegment]: ...
