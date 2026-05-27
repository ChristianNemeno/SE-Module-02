# app/services/go3/prosody_detector.py
import logging
from typing import Any

import librosa  # type: ignore[import-untyped]
import numpy as np
import parselmouth  # type: ignore[import-untyped]

from app.models.prosody_detector import ProsodyFlags

_INAUDIBLE_RMS_THRESHOLD = 0.01
_MONOTONE_F0_STD_THRESHOLD = 30.0       # Hz — empirical: humans trying to read flat sit ~25-40Hz (lexical stress + breath groups); expressive reading 38-69Hz; raw neural TTS 15-25Hz. 30Hz catches deliberate flat human speech while leaving normal expressive reading above the bar.
_MIN_DURATION_SECONDS = 5.0
_MIN_VOICED_FRAMES = 10
_SAMPLE_RATE = 16000
_SILENCE_RMS_THRESHOLD: float = 0.015      # frames below this = silence; above noise floor (~0.005), below soft speech (~0.03)
_SILENCE_MIN_FRAMES: int = 6               # min consecutive silent frames to count as inter-word gap (~192ms at hop=512, sr=16000)
_MEDIUM_GAP_MAX: float = 0.5               # upper bound on "within-sentence" word gap (s); longer = sentence break / breath
_WORD_BY_WORD_RATE_THRESHOLD: float = 0.2  # medium gaps / total audio duration > 0.2/s = word-by-word; calibrated on fluent (0.11/s) vs WBW (0.30/s) fixtures
_MIN_GAP_EVENTS: int = 2                   # need ≥2 interior gaps to compute a meaningful rate

_LOG = logging.getLogger(__name__)


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
        """True if mean inter-word silence gap exceeds threshold — indicates halting, word-by-word pacing."""
        hop_length: int = 512
        rms: np.ndarray = librosa.feature.rms(  # type: ignore[no-untyped-call]
            y=y, frame_length=2048, hop_length=hop_length
        )[0]
        n_frames: int = len(rms)
        silent_mask: np.ndarray = rms < _SILENCE_RMS_THRESHOLD

        transitions: np.ndarray = np.diff(silent_mask.astype(np.int8))
        gap_starts: np.ndarray = np.where(transitions == 1)[0] + 1
        gap_ends: np.ndarray = np.where(transitions == -1)[0] + 1

        if silent_mask[0]:
            gap_starts = np.concatenate([[0], gap_starts])
        if silent_mask[-1]:
            gap_ends = np.concatenate([gap_ends, [n_frames]])

        n_gaps: int = min(len(gap_starts), len(gap_ends))
        gap_starts = gap_starts[:n_gaps]
        gap_ends = gap_ends[:n_gaps]

        # Keep only interior gaps — exclude leading/trailing recording silence
        interior: np.ndarray = (gap_starts > 0) & (gap_ends < n_frames)
        gap_lengths: np.ndarray = (gap_ends - gap_starts)[interior]
        real_gaps: np.ndarray = gap_lengths[gap_lengths >= _SILENCE_MIN_FRAMES]

        if len(real_gaps) < _MIN_GAP_EVENTS:
            _LOG.info(
                "word_by_word diagnostics: raw_runs=%d interior_gaps=%d (need >=%d) -> decision=False (insufficient gaps)",
                n_gaps, len(real_gaps), _MIN_GAP_EVENTS,
            )
            return False

        frame_duration: float = hop_length / float(sr)
        gap_durations: np.ndarray = real_gaps * frame_duration
        total_duration: float = n_frames * frame_duration
        medium_count: int = int(np.sum(gap_durations <= _MEDIUM_GAP_MAX))
        medium_rate: float = medium_count / total_duration if total_duration > 0 else 0.0
        decision: bool = medium_rate > _WORD_BY_WORD_RATE_THRESHOLD
        _LOG.info(
            "word_by_word diagnostics: raw_runs=%d interior_gaps=%d medium_gaps=%d "
            "total_duration=%.2fs medium_rate=%.3f/s durations=%s "
            "min=%.3f median=%.3f mean=%.3f max=%.3f threshold=%.3f/s -> decision=%s",
            n_gaps,
            len(real_gaps),
            medium_count,
            total_duration,
            medium_rate,
            [round(float(g), 3) for g in gap_durations],
            float(np.min(gap_durations)),
            float(np.median(gap_durations)),
            float(np.mean(gap_durations)),
            float(np.max(gap_durations)),
            _WORD_BY_WORD_RATE_THRESHOLD,
            decision,
        )
        return decision
