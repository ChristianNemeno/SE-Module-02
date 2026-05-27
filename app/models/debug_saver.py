from typing import Protocol

from app.models.assessment import AssessmentResult


class DebugSaverProtocol(Protocol):
    """Interface for debug artifact persistence — orchestrator depends on this, not the concrete."""

    def save(
        self,
        wav_path: str,
        result: AssessmentResult,
        passage_id: str,
        learner_id: str,
    ) -> None:
        """Persist WAV + result JSON for a completed analysis run."""
        ...


class NullDebugSaver:
    """No-op debug saver — used when DEBUG_AUDIO_DIR is not configured."""

    def save(
        self,
        wav_path: str,
        result: AssessmentResult,
        passage_id: str,
        learner_id: str,
    ) -> None:
        """Does nothing."""
        del wav_path, result, passage_id, learner_id
