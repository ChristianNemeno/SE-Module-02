# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false
"""Download HF audio fixtures for monotone-detector testing.

Fetches 5 natural-prosody WAVs from hf-internal-testing/librispeech_asr_dummy
into tests/fixtures/prosody_samples/expected_false/, and 5 synthesized WAVs
from facebook/mms-tts-eng into expected_true_monotone/.

MMS-TTS alone may not push F0 std dev below the detector's 20Hz threshold,
so any clip whose F0 std dev measures >=20Hz gets pitch-flattened via
parselmouth so the monotone detector trips.

Safe to re-run — skips if all 10 fixtures exist unless --force is passed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
import parselmouth  # type: ignore[import-untyped]
import soundfile as sf
import torch
from datasets import load_dataset
from parselmouth.praat import call  # type: ignore[import-untyped]
from transformers import AutoTokenizer, VitsModel

_SAMPLE_RATE = 16000
_MIN_DURATION_S = 5.5
_F0_FLATTEN_THRESHOLD_HZ = 20.0
_REPO_ROOT = Path(__file__).resolve().parent.parent
_OUT_ROOT = _REPO_ROOT / "tests" / "fixtures" / "prosody_samples"
_FALSE_DIR = _OUT_ROOT / "expected_false"
_TRUE_DIR = _OUT_ROOT / "expected_true_monotone"

_TTS_SENTENCES: list[str] = [
    "The cat sat on the brown mat near the door, watching the rain fall outside while the wind blew softly through the open window.",
    "A small boy walked along the river path, carrying a basket of apples for his grandmother who lived in a small cottage by the woods.",
    "She opened the book on the wooden table and began to read aloud to the children who were sitting quietly on the carpet near the fireplace.",
    "The teacher asked the class to be quiet so everyone could hear the morning announcements about the upcoming school field trip next week.",
    "Birds were singing in the tall green trees while the warm sun rose above the hills and the morning mist began to fade slowly away.",
]


def _measure_f0_std(wav_path: Path) -> float:
    """Returns F0 std dev (Hz) over voiced frames. Mirrors detector's own logic."""
    snd: Any = parselmouth.Sound(str(wav_path))  # type: ignore[no-untyped-call]
    pitch: Any = snd.to_pitch()  # type: ignore[no-untyped-call]
    f0: np.ndarray = np.array(pitch.selected_array["frequency"])
    voiced = f0[f0 > 0]
    return float(np.std(voiced)) if len(voiced) >= 10 else 0.0


def _flatten_pitch(wav_path: Path) -> None:
    """In-place: replace F0 contour with its mean — drops std dev to ~0."""
    snd: Any = parselmouth.Sound(str(wav_path))  # type: ignore[no-untyped-call]
    manipulation: Any = call(snd, "To Manipulation", 0.01, 75, 600)
    pitch_tier: Any = call(manipulation, "Extract pitch tier")
    n_points: int = int(call(pitch_tier, "Get number of points"))
    if n_points == 0:
        return
    mean_f0: float = float(call(pitch_tier, "Get mean (points)", 0.0, 0.0))
    call(pitch_tier, "Formula", f"{mean_f0}")
    call([pitch_tier, manipulation], "Replace pitch tier")
    new_snd: Any = call(manipulation, "Get resynthesis (overlap-add)")
    new_array: np.ndarray = np.asarray(new_snd.values).flatten().astype(np.float32)
    sf.write(str(wav_path), new_array, _SAMPLE_RATE, subtype="PCM_16")


class LibriSpeechFetcher:
    """Loads hf-internal-testing/librispeech_asr_dummy and writes first N samples >= min duration as 16kHz mono WAVs."""

    def fetch(self, out_dir: Path, n: int = 5, min_duration_s: float = _MIN_DURATION_S) -> list[Path]:
        """Returns list of written WAV paths. Raises if not enough qualifying samples are found."""
        out_dir.mkdir(parents=True, exist_ok=True)
        ds: Any = load_dataset(
            "hf-internal-testing/librispeech_asr_dummy", "clean", split="validation"
        )
        written: list[Path] = []
        for sample in ds:
            if len(written) >= n:
                break
            audio = sample["audio"]
            array: np.ndarray = np.asarray(audio["array"], dtype=np.float32)
            sr = int(audio["sampling_rate"])
            if len(array) / sr < min_duration_s:
                continue
            if sr != _SAMPLE_RATE:
                raise RuntimeError(f"unexpected sample rate {sr}; expected {_SAMPLE_RATE}")
            path = out_dir / f"librispeech_{len(written) + 1:02d}.wav"
            sf.write(str(path), array, _SAMPLE_RATE, subtype="PCM_16")
            written.append(path)
        if len(written) < n:
            raise RuntimeError(f"only found {len(written)} qualifying samples; need {n}")
        return written


class MmsTtsSynthesizer:
    """Loads facebook/mms-tts-eng once; synthesizes each sentence as 16kHz mono WAV.
    Post-processes with pitch flattening if raw F0 std dev meets/exceeds the threshold."""

    def __init__(self, sentences: list[str], flatten_if_above_hz: float = _F0_FLATTEN_THRESHOLD_HZ) -> None:
        self._sentences = sentences
        self._threshold = flatten_if_above_hz
        self._model: VitsModel | None = None
        self._tokenizer: Any = None

    def _load(self) -> None:
        if self._model is None:
            self._model = VitsModel.from_pretrained("facebook/mms-tts-eng")
            self._tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-eng")

    def synthesize(self, out_dir: Path) -> list[tuple[Path, float, bool]]:
        """Returns (path, final_f0_std_hz, was_flattened) per sample."""
        out_dir.mkdir(parents=True, exist_ok=True)
        self._load()
        assert self._model is not None and self._tokenizer is not None
        results: list[tuple[Path, float, bool]] = []
        for idx, text in enumerate(self._sentences, start=1):
            inputs = self._tokenizer(text, return_tensors="pt")
            with torch.no_grad():
                output = self._model(**inputs).waveform
            audio: np.ndarray = output[0].cpu().numpy().astype(np.float32)
            sr = int(self._model.config.sampling_rate)
            if sr != _SAMPLE_RATE:
                raise RuntimeError(f"MMS-TTS sample rate {sr} != expected {_SAMPLE_RATE}")
            path = out_dir / f"mms_tts_{idx:02d}.wav"
            sf.write(str(path), audio, _SAMPLE_RATE, subtype="PCM_16")
            # Always flatten — drops F0 std dev to near-0 deterministically, avoids boundary cases at the 20Hz threshold
            _flatten_pitch(path)
            std_hz = _measure_f0_std(path)
            flattened = True
            duration_s = len(audio) / _SAMPLE_RATE
            if duration_s < 5.5:
                raise RuntimeError(
                    f"{path.name} synthesized at {duration_s:.2f}s — below 5.5s safety margin "
                    f"for detector's 5.0s gate; lengthen sentence #{idx}"
                )
            results.append((path, std_hz, flattened))
        return results


def _already_present() -> bool:
    expected = [_FALSE_DIR / f"librispeech_{i:02d}.wav" for i in range(1, 6)]
    expected += [_TRUE_DIR / f"mms_tts_{i:02d}.wav" for i in range(1, 6)]
    return all(p.exists() for p in expected)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Regenerate even if all fixtures exist")
    args = parser.parse_args()

    if not args.force and _already_present():
        print("All 10 fixtures already present. Use --force to regenerate.")
        return 0

    print("=== Fetching LibriSpeech (expected monotone=False) ===")
    for p in LibriSpeechFetcher().fetch(_FALSE_DIR):
        std = _measure_f0_std(p)
        marker = "OK" if std > _F0_FLATTEN_THRESHOLD_HZ else "WARN low F0 var"
        print(f"  {p.relative_to(_REPO_ROOT)}  F0_std={std:.1f}Hz  {marker}")

    print("\n=== Synthesizing MMS-TTS (expected monotone=True) ===")
    for path, std_hz, flattened in MmsTtsSynthesizer(_TTS_SENTENCES).synthesize(_TRUE_DIR):
        tag = "[flattened]" if flattened else "[raw]"
        marker = "OK" if std_hz < _F0_FLATTEN_THRESHOLD_HZ else "FAIL would not trip"
        print(f"  {path.relative_to(_REPO_ROOT)}  F0_std={std_hz:.1f}Hz {tag}  {marker}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
