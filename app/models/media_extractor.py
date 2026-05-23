from typing import Protocol, TypedDict


class ExtractionResult(TypedDict):
    """Paths to the extracted WAV and normalized MP4 produced by ffmpeg."""

    wav_path: str
    mp4_path: str


class MediaExtractorProtocol(Protocol):
    """Interface for extracting audio/video from an uploaded file."""

    def extract(self, source_path: str, out_dir: str) -> ExtractionResult:
        """Extract WAV + MP4 into out_dir. Raises RuntimeError on ffmpeg failure."""
        ...
