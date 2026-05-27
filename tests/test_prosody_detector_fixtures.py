"""Runs the real ProsodyAmplitudeDetector against the curated HF fixtures.

False set: LibriSpeech audiobook clips — natural prosody, monotone must be False.
True set: MMS-TTS clips (pitch-flattened) — monotone must be True.

Skips the whole module if fixtures aren't present.
Regenerate with: python tools/download_prosody_fixtures.py
"""

from pathlib import Path

import pytest

_FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "prosody_samples"
_FALSE_DIR = _FIXTURE_ROOT / "expected_false"
_TRUE_DIR = _FIXTURE_ROOT / "expected_true_monotone"

if not _FALSE_DIR.exists() or not _TRUE_DIR.exists():
    pytest.skip(
        "prosody fixtures missing — run tools/download_prosody_fixtures.py",
        allow_module_level=True,
    )

from app.services.go3.prosody_detector import ProsodyAmplitudeDetector  # noqa: E402

_FALSE_WAVS = sorted(_FALSE_DIR.glob("*.wav"))
_TRUE_WAVS = sorted(_TRUE_DIR.glob("*.wav"))


@pytest.mark.parametrize("wav", _FALSE_WAVS, ids=lambda p: p.name)
def test_false_samples_do_not_trip_monotone(wav: Path) -> None:
    """LibriSpeech natural reading should keep monotone_reading=False."""
    flags = ProsodyAmplitudeDetector().detect(str(wav))
    assert flags["monotone_reading"] is False, f"{wav.name} unexpectedly tripped"


@pytest.mark.parametrize("wav", _TRUE_WAVS, ids=lambda p: p.name)
def test_true_samples_trip_monotone(wav: Path) -> None:
    """Pitch-flattened TTS should trip monotone_reading=True."""
    flags = ProsodyAmplitudeDetector().detect(str(wav))
    assert flags["monotone_reading"] is True, f"{wav.name} did not trip"
