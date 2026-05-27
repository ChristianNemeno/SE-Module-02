import json
import logging
import os
import re
import shutil
from datetime import datetime

from app.models.assessment import AssessmentResult

logger = logging.getLogger(__name__)

_SAFE_RE = re.compile(r"[^A-Za-z0-9_.\-]")


def _safe(value: str) -> str:
    """Strip non-filename-safe chars and truncate to 64 chars."""
    return _SAFE_RE.sub("_", value)[:64] or "anon"


class AudioDebugSaver:
    """Copies WAV + writes companion JSON to a persistent debug directory after each analysis."""

    def __init__(self, debug_dir: str) -> None:
        """Create debug_dir if it doesn't exist. Resolves to absolute path."""
        self._debug_dir = os.path.realpath(debug_dir)
        os.makedirs(self._debug_dir, exist_ok=True)

    def save(
        self,
        wav_path: str,
        result: AssessmentResult,
        passage_id: str,
        learner_id: str,
    ) -> None:
        """Copy WAV and write companion JSON. Raises ValueError if resolved path escapes debug_dir."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = f"{timestamp}_{_safe(passage_id)}_{_safe(learner_id) or 'anon'}"
        wav_dest = os.path.join(self._debug_dir, f"{stem}.wav")
        json_dest = os.path.join(self._debug_dir, f"{stem}.json")

        # Guard against path traversal — should never fire after _safe(), but belt-and-suspenders
        boundary = self._debug_dir + os.sep
        if not os.path.realpath(wav_dest).startswith(boundary):
            raise ValueError(f"path traversal detected: {wav_dest!r}")

        shutil.copy(wav_path, wav_dest)
        with open(json_dest, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=2)
        logger.info("debug artifacts saved: %s", wav_dest)
