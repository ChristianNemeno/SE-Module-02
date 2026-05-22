from typing import Any

from app.models.assessment import AssessmentResult

REQUIRED_GO2_FIELDS: list[str] = [
    "wpm", "word_recognition_pct", "reading_level",
    "correct", "mispronunciation", "substitution",
    "omission", "insertion", "repetition", "refusal_to_pronounce",
]
REQUIRED_GO3_FIELDS: list[str] = [
    "finger_pointing", "loss_of_place", "monotone_reading",
    "word_by_word_reading", "inaudible_reading",
]


class ResultConsolidator:
    """Merges GO2 and GO3 pipeline results into a single validated AssessmentResult."""

    @staticmethod
    def merge(go2_result: dict[str, Any], go3_result: dict[str, Any]) -> AssessmentResult:
        """Merges GO2 and GO3 dicts, validates all 15 required fields are present and non-None."""
        merged: dict[str, Any] = {**go2_result, **go3_result}
        all_required = REQUIRED_GO2_FIELDS + REQUIRED_GO3_FIELDS
        missing = [f for f in all_required if f not in merged or merged[f] is None]
        if missing:
            raise ValueError(f"ResultConsolidator: missing required fields: {missing}")
        return AssessmentResult.model_validate(merged)
