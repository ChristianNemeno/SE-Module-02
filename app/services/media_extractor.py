import os
import subprocess

from app.models.media_extractor import ExtractionResult


class MediaExtractor:
    """Extracts a 16 kHz mono WAV and a normalized MP4 from an uploaded video file."""

    def extract(self, source_path: str, out_dir: str) -> ExtractionResult:
        """Run ffmpeg to produce audio.wav and video.mp4 in out_dir. Raises RuntimeError on failure."""
        wav_path = os.path.join(out_dir, "audio.wav")
        mp4_path = os.path.join(out_dir, "video.mp4")

        self._run(
            "ffmpeg", "-y", "-i", source_path,
            "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
            wav_path,
        )
        self._run(
            "ffmpeg", "-y", "-i", source_path,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-an",
            mp4_path,
        )
        return ExtractionResult(wav_path=wav_path, mp4_path=mp4_path)

    def _run(self, *args: str) -> None:
        """Run a subprocess command. Raises RuntimeError with stderr on non-zero exit."""
        try:
            subprocess.run(list(args), check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                f"FFmpeg failed: {exc.stderr.decode(errors='replace')}"
            ) from exc
