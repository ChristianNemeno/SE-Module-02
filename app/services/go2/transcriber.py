from typing import Any

import whisperx  # type: ignore[import-untyped]

from app.models.transcription import WordSegment


class WhisperXTranscriber:
    """
    Holds pre-loaded WhisperX model refs ug runs forced-alignment transcription.

    Dili i-load ang models per request — gi-init once sa startup via load().
    """

    def __init__(self) -> None:
        self._model: Any = None
        self._align_model: Any = None
        self._metadata: Any = None

    def load(self) -> None:
        """Loads the WhisperX base model ug alignment model into memory. Called once sa lifespan startup."""
        self._model = whisperx.load_model(  # type: ignore[no-untyped-call]
            "base", device="cpu", language="en"
        )
        self._align_model, self._metadata = whisperx.load_align_model(  # type: ignore[no-untyped-call]
            language_code="en", device="cpu"
        )

    def transcribe(self, wav_path: str, passage_text: str) -> list[WordSegment]:
        """
        Transcribes a WAV file ug returns word-level timestamps via forced alignment.

        Returns empty list kung walay word_segments sa aligned output (e.g., silence gap).
        """
        result = self._model.transcribe(wav_path, batch_size=4)  # type: ignore[no-untyped-call]
        aligned = whisperx.align(  # type: ignore[no-untyped-call]
            result["segments"],
            self._align_model,
            self._metadata,
            wav_path,
            device="cpu",
        )
        words: list[WordSegment] = []
        for seg in aligned.get("word_segments", []):
            words.append(
                WordSegment(
                    word=seg["word"].lower().strip(),
                    start=seg["start"],
                    end=seg["end"],
                    score=seg.get("score", 1.0),
                )
            )
        return words


_transcriber: WhisperXTranscriber | None = None


def load_models() -> None:
    """Creates ug loads the WhisperXTranscriber singleton. Called once sa FastAPI lifespan."""
    global _transcriber
    _transcriber = WhisperXTranscriber()
    _transcriber.load()


def get_transcriber_instance() -> WhisperXTranscriber:
    """Returns the singleton transcriber. Mo-raise og RuntimeError kung wala pa ma-load sa startup."""
    if _transcriber is None:
        raise RuntimeError("Transcriber not loaded — call load_models() at startup")
    return _transcriber
