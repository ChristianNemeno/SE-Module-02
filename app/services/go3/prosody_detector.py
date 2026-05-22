# app/services/go3/prosody_detector.py
from typing import Any

import librosa  # type: ignore[import-untyped]
import numpy as np
import parselmouth  # type: ignore[import-untyped]

from app.models.prosody_detector import ProsodyFlags

_INAUDIBLE_RMS_THRESHOLD = 0.01
_MONOTONE_F0_STD_THRESHOLD = 20.0   # Hz
_WORD_BY_WORD_IOI_THRESHOLD = 0.8   # seconds
_MIN_DURATION_SECONDS = 5.0
_MIN_VOICED_FRAMES = 10
_MIN_ONSET_EVENTS = 3
_SAMPLE_RATE = 16000


def _default_flags() -> ProsodyFlags:
    """Safe all-False result — used when audio is too short to analyze."""
    return {"inaudible_reading": False, "monotone_reading": False, "word_by_word_reading": False}


class ProsodyAmplitudeDetector:
    """Extracts three prosody-based behavioral flags from a WAV file using librosa and parselmouth."""

    def detect(self, wav_path: str) -> ProsodyFlags:
        """Loads WAV once and runs all three prosody checks. Returns all-False for audio < 5s."""
        y: np.ndarray
        sr: int | float
        y, sr = librosa.load(wav_path, sr=_SAMPLE_RATE)  # type: ignore[no-untyped-call]
        if len(y) / sr < _MIN_DURATION_SECONDS:
            return _default_flags()
        return {
            "inaudible_reading": self._detect_inaudible(y),
            "monotone_reading": self._detect_monotone(wav_path),
            "word_by_word_reading": self._detect_word_by_word(y, sr),
        }

    def _detect_inaudible(self, y: np.ndarray) -> bool:
        """True if mean RMS energy falls below threshold — indicates voice too soft to score."""
        rms: np.ndarray = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]  # type: ignore[no-untyped-call]
        return float(np.mean(rms)) < _INAUDIBLE_RMS_THRESHOLD

    def _detect_monotone(self, wav_path: str) -> bool:
        """True if F0 standard deviation is below threshold — indicates flat/unexpressive reading."""
        snd: Any = parselmouth.Sound(wav_path)  # type: ignore[no-untyped-call]
        pitch: Any = snd.to_pitch()  # type: ignore[no-untyped-call]
        f0_values: np.ndarray = np.array(pitch.selected_array["frequency"])  # type: ignore[no-untyped-call]
        voiced: np.ndarray = f0_values[f0_values > 0]
        if len(voiced) < _MIN_VOICED_FRAMES:
            return False
        return float(np.std(voiced)) < _MONOTONE_F0_STD_THRESHOLD

    def _detect_word_by_word(self, y: np.ndarray, sr: int | float) -> bool:
        """True if mean inter-onset interval exceeds threshold — indicates halting, word-by-word pacing."""
        onsets: np.ndarray = librosa.onset.onset_detect(y=y, sr=sr, units="time")  # type: ignore[no-untyped-call]
        if len(onsets) < _MIN_ONSET_EVENTS:
            return False
        iois: np.ndarray = np.diff(onsets)
        return float(np.mean(iois)) > _WORD_BY_WORD_IOI_THRESHOLD
