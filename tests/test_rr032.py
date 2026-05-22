from typing import Any

import pytest

from app.models.assessment import AssessmentResult
from app.utils.result_consolidator import ResultConsolidator


def _go2() -> dict[str, Any]:
    return {
        "wpm": 80.0,
        "word_recognition_pct": 92.0,
        "reading_level": "Instructional",
        "correct": 46,
        "mispronunciation": 2,
        "substitution": 1,
        "omission": 1,
        "insertion": 0,
        "repetition": 1,
        "refusal_to_pronounce": 0,
    }


def _go3() -> dict[str, Any]:
    return {
        "finger_pointing": False,
        "loss_of_place": True,
        "monotone_reading": False,
        "word_by_word_reading": False,
        "inaudible_reading": False,
    }


def test_valid_merge_returns_assessment_result() -> None:
    """Valid GO2 + GO3 dicts produce a fully-populated AssessmentResult."""
    result = ResultConsolidator.merge(_go2(), _go3())
    assert isinstance(result, AssessmentResult)
    assert result.wpm == 80.0
    assert result.reading_level == "Instructional"
    assert result.loss_of_place is True
    assert len(result.model_dump()) == 15


def test_missing_field_raises_value_error() -> None:
    """Omitting a required GO2 field raises ValueError."""
    go2 = _go2()
    del go2["wpm"]
    with pytest.raises(ValueError, match="missing required fields"):
        ResultConsolidator.merge(go2, _go3())


def test_none_field_raises_value_error() -> None:
    """A required field set to None raises ValueError."""
    go3 = _go3()
    go3["finger_pointing"] = None
    with pytest.raises(ValueError, match="missing required fields"):
        ResultConsolidator.merge(_go2(), go3)
