from typing import Any

from app.models.assessment import AssessmentResult


class ResultConsolidator:
    """Merges GO2 ug GO3 pipeline results into a single AssessmentResult. Wired in RR-020."""

    def merge(self, go2_result: dict[str, Any], go3_result: dict[str, Any]) -> AssessmentResult:
        """Combines go2_result ug go3_result. Dili pa implemented — RR-020 ra ni."""
        raise NotImplementedError
