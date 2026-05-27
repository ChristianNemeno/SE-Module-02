# tools/inspect_transcription.py
"""Run WhisperX ASR + forced alignment on a single recording and dump word-level results to CSV.

Usage:
    python tools/inspect_transcription.py path/to/recording.wav --passage-file path/to/passage.txt
    python tools/inspect_transcription.py recording.mp4 --passage-file passage.txt --out run.csv --model large-v3

Bypasses /analyze entirely — exercises only Layer 1 (transcriber.py) so timing, score, and
word-string issues can be debugged in isolation. CSV columns: index, word, start, end, duration, score.
"""
from __future__ import annotations

import argparse
import csv
import logging
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

# Allow running as a script: add repo root so `from app...` resolves.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.models.transcription import WordSegment  # noqa: E402
from app.services.go2.transcriber import WhisperXTranscriber  # noqa: E402

_LOG = logging.getLogger("inspect_transcription")


def _default_out_path(audio_path: Path) -> Path:
    """Sibling CSV next to the input audio: foo.wav -> foo.transcription.csv."""
    return audio_path.with_suffix("").with_name(f"{audio_path.stem}.transcription.csv")


def _resolve_wav(audio_path: Path, tmp_dir: str) -> str:
    """Return a WAV path for the input. For non-.wav files, transcodes audio only.

    MediaExtractor isn't used here because it also encodes an MP4 video stream — that
    fails on audio-only inputs (e.g. .m4a). Layer-1 inspection only needs the WAV.
    """
    if audio_path.suffix.lower() == ".wav":
        return str(audio_path)
    wav_path = str(Path(tmp_dir) / "audio.wav")
    _LOG.info("non-WAV input %s — transcoding to %s", audio_path.name, wav_path)
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(audio_path),
                "-vn", "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
                wav_path,
            ],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"FFmpeg failed: {exc.stderr.decode(errors='replace')}"
        ) from exc
    return wav_path


def _write_csv(out_path: Path, words: list[WordSegment]) -> None:
    """Write one row per WordSegment with a computed `duration` column."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["index", "word", "start", "end", "duration", "score"])
        for i, w in enumerate(words):
            writer.writerow([i, w["word"], w["start"], w["end"], w["end"] - w["start"], w["score"]])


def _print_summary(out_path: Path, words: list[WordSegment]) -> None:
    """Stdout summary so the user gets a quick health read without opening the CSV."""
    print(f"wrote {len(words)} words to {out_path}")
    if not words:
        print("no word segments produced — check input audio and passage text")
        return
    scores = [w["score"] for w in words]
    total = words[-1]["end"] - words[0]["start"]
    print(
        f"score min={min(scores):.3f} mean={statistics.fmean(scores):.3f} max={max(scores):.3f} | "
        f"span={total:.2f}s"
    )


def main() -> int:
    """CLI entrypoint. Returns 0 success, 2 if an input file is missing."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "audio_path",
        type=Path,
        help="Path to a WAV, MP4, or any ffmpeg-supported audio/video file.",
    )
    parser.add_argument(
        "--passage-file",
        type=Path,
        required=True,
        help="UTF-8 text file containing the passage that was supposed to be read.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="CSV output path. Default: <audio>.transcription.csv next to the input audio file.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override WHISPERX_MODEL for this run (e.g. base, large-v3).",
    )
    args = parser.parse_args()

    if not args.audio_path.exists():
        print(f"audio file not found: {args.audio_path}", file=sys.stderr)
        return 2
    if not args.passage_file.exists():
        print(f"passage file not found: {args.passage_file}", file=sys.stderr)
        return 2

    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s - %(levelname)s - %(message)s",
    )

    passage_text = args.passage_file.read_text(encoding="utf-8")
    out_path: Path = args.out if args.out is not None else _default_out_path(args.audio_path)

    if args.model is not None:
        # get_settings() is lru_cached — mutating the cached instance affects subsequent reads
        # made inside WhisperXTranscriber.load(). Pydantic BaseSettings is mutable by default.
        get_settings().WHISPERX_MODEL = args.model
        _LOG.info("overriding WHISPERX_MODEL=%s for this run", args.model)

    tmp_dir = tempfile.mkdtemp(prefix="inspect_transcription_")
    try:
        wav_path = _resolve_wav(args.audio_path, tmp_dir)
        transcriber = WhisperXTranscriber()
        transcriber.load()
        words = transcriber.transcribe(wav_path, passage_text)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    _write_csv(out_path, words)
    _print_summary(out_path, words)
    return 0


if __name__ == "__main__":
    sys.exit(main())
