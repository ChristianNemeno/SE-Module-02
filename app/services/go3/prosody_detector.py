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
_MIN_SPEECH_FRAMES: int = 4                # ignore speech blips < ~128ms (hop=512, sr=16000) — noise/breath, not words
_WBW_SILENCE_RATIO_THRESHOLD: float = 0.40 # silent frames / total >= 40% = halting reader; calibrated fluent 33-39%, WBW 41-58%
_WBW_SPEECH_RATE_THRESHOLD: float = 1.0    # speech segments / second < 1.0 = slow pacing; calibrated fluent 0.96-1.43/s, WBW 0.79-0.96/s

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
        """True if recording shows high silence ratio AND low speech-segment rate — halting word-by-word pacing."""
        hop_length: int = 512
        rms: np.ndarray = librosa.feature.rms(  # type: ignore[no-untyped-call]
            y=y, frame_length=2048, hop_length=hop_length
        )[0]
        n_frames: int = len(rms)
        if n_frames == 0:
            return False

        silent_mask: np.ndarray = rms < _SILENCE_RMS_THRESHOLD
        silence_ratio: float = float(np.sum(silent_mask)) / n_frames

        # Count speech segments — runs of non-silent frames of meaningful length
        speech_mask: np.ndarray = ~silent_mask
        transitions: np.ndarray = np.diff(speech_mask.astype(np.int8))
        seg_starts: np.ndarray = np.where(transitions == 1)[0] + 1
        seg_ends: np.ndarray = np.where(transitions == -1)[0] + 1
        if speech_mask[0]:
            seg_starts = np.concatenate([[0], seg_starts])
        if speech_mask[-1]:
            seg_ends = np.concatenate([seg_ends, [n_frames]])
        n_runs: int = min(len(seg_starts), len(seg_ends))
        seg_lengths: np.ndarray = seg_ends[:n_runs] - seg_starts[:n_runs]
        n_speech_segments: int = int(np.sum(seg_lengths >= _MIN_SPEECH_FRAMES))

        frame_duration: float = hop_length / float(sr)
        total_duration: float = n_frames * frame_duration
        speech_rate: float = n_speech_segments / total_duration if total_duration > 0 else 0.0

        decision: bool = (
            silence_ratio >= _WBW_SILENCE_RATIO_THRESHOLD
            and speech_rate < _WBW_SPEECH_RATE_THRESHOLD
        )
        _LOG.info(
            "word_by_word diagnostics: silence_ratio=%.3f speech_rate=%.3f seg/s "
            "(n_segments=%d duration=%.2fs) thresholds=(silence>=%.2f, speech<%.2f) -> decision=%s",
            silence_ratio,
            speech_rate,
            n_speech_segments,
            total_duration,
            _WBW_SILENCE_RATIO_THRESHOLD,
            _WBW_SPEECH_RATE_THRESHOLD,
            decision,
        )
        return decision
