"""Runs the real ProsodyAmplitudeDetector against the curated word_by_word fixtures.

False set: a fluent reading should keep word_by_word_reading=False.
True set: a deliberately word-by-word reading should trip word_by_word_reading=True.

Skips the whole module if fixtures aren't present.
"""

from pathlib import Path

import pytest

_FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "word_by_word_samples"
_FALSE_DIR = _FIXTURE_ROOT / "expected_false"
_TRUE_DIR = _FIXTURE_ROOT / "expected_true"

if not _FALSE_DIR.exists() or not _TRUE_DIR.exists():
    pytest.skip(
        "word_by_word fixtures missing",
        allow_module_level=True,
    )

from app.services.go3.prosody_detector import ProsodyAmplitudeDetector  # noqa: E402

_FALSE_WAVS = sorted(_FALSE_DIR.glob("*.wav"))
_TRUE_WAVS = sorted(_TRUE_DIR.glob("*.wav"))


@pytest.mark.parametrize("wav", _FALSE_WAVS, ids=lambda p: p.name)
def test_false_samples_do_not_trip_word_by_word(wav: Path) -> None:
    """Fluent reading should keep word_by_word_reading=False."""
    flags = ProsodyAmplitudeDetector().detect(str(wav))
    assert flags["word_by_word_reading"] is False, f"{wav.name} unexpectedly tripped"


@pytest.mark.parametrize("wav", _TRUE_WAVS, ids=lambda p: p.name)
def test_true_samples_trip_word_by_word(wav: Path) -> None:
    """Deliberately word-by-word reading should trip word_by_word_reading=True."""
    flags = ProsodyAmplitudeDetector().detect(str(wav))
    assert flags["word_by_word_reading"] is True, f"{wav.name} did not trip"
