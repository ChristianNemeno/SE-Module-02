from fastapi import APIRouter, Form, Header, HTTPException, UploadFile

from app.config import get_settings
from app.models.assessment import AssessmentResult


class AnalyzeController:
    """Handles HTTP for POST /analyze only. No business logic."""

    def __init__(self) -> None:
        self.router = APIRouter(tags=["analyze"])
        self.router.add_api_route(
            "/analyze",
            self.analyze,
            methods=["POST"],
            response_model=AssessmentResult,
        )

    async def analyze(
        self,
        file: UploadFile,
        passage_id: str = Form(...),
        x_api_key: str = Header(..., alias="X-API-Key"),
    ) -> AssessmentResult:
        """Accepts a video upload, validates API key, returns stub AssessmentResult. Raises 401 if key is wrong."""
        self._check_api_key(x_api_key)
        return AssessmentResult(
            wpm=85.5,
            word_recognition_pct=92.3,
            reading_level="Instructional",
            correct=48,
            mispronunciation=2,
            substitution=1,
            omission=1,
            insertion=0,
            repetition=0,
            refusal_to_pronounce=0,
            finger_pointing=False,
            lip_movement=False,
            head_movement=False,
            voice_too_soft=False,
            loses_place=False,
        )

    def _check_api_key(self, key: str) -> None:
        """Raises 401 if X-API-Key doesn't match settings."""
        if key != get_settings().API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
