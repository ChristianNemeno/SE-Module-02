# tools/inspect_word_by_word.py
"""Run ProsodyAmplitudeDetector against a single audio file and dump word_by_word diagnostics.

Usage:
    python tools/inspect_word_by_word.py path/to/recording.wav

Configures logging at INFO so the detector's own _LOG.info() lines surface, then
prints the returned flags dict. No new gap-stats code lives here — just an entry point.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Allow running as a script: add repo root so `from app...` resolves.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.go3.prosody_detector import ProsodyAmplitudeDetector  # noqa: E402


def main() -> int:
    """CLI entrypoint. Returns 0 on success, 2 if the file is missing."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "wav_path",
        type=Path,
        help="Path to a WAV (or any librosa-supported audio file).",
    )
    args = parser.parse_args()

    if not args.wav_path.exists():
        print(f"file not found: {args.wav_path}", file=sys.stderr)
        return 2

    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s - %(levelname)s - %(message)s",
    )

    flags = ProsodyAmplitudeDetector().detect(str(args.wav_path))
    print()
    print(f"flags: {flags}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
