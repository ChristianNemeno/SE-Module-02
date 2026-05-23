from fastapi import APIRouter, Depends, Form, Header, HTTPException, UploadFile

from app.config import get_settings
from app.dependencies import get_analysis_orchestrator
from app.models.assessment import AssessmentResult
from app.services.analysis_orchestrator import AnalysisOrchestrator


class AnalyzeController:
    """Handles HTTP for POST /analyze only. Delegates all pipeline logic to AnalysisOrchestrator."""

    def __init__(self) -> None:
        """Register the /analyze route."""
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
        learner_id: str = Form(""),
        x_api_key: str = Header(..., alias="X-API-Key"),
        orchestrator: AnalysisOrchestrator = Depends(get_analysis_orchestrator),
    ) -> AssessmentResult:
        """Accept a video upload and run the full assessment pipeline."""
        self._check_api_key(x_api_key)
        upload_bytes = await file.read()
        filename = file.filename or "upload.webm"
        return await orchestrator.run(upload_bytes, filename, passage_id, learner_id)

    def _check_api_key(self, key: str) -> None:
        """Raises 401 if X-API-Key doesn't match settings."""
        if key != get_settings().API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
