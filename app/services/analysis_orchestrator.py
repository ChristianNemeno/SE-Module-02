import asyncio
import logging
import os
import shutil
import tempfile

from fastapi import HTTPException

from app.models.assessment import AssessmentResult
from app.models.debug_saver import DebugSaverProtocol, NullDebugSaver
from app.models.media_extractor import MediaExtractorProtocol
from app.models.session import SessionRecord, SessionRepositoryProtocol
from app.services.go2.pipeline import GO2Pipeline
from app.services.go3.pipeline import GO3Pipeline
from app.utils.result_consolidator import ResultConsolidator

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """Async coordinator: save temp file → extract media → run GO2+GO3 in parallel → merge → DB insert."""

    def __init__(
        self,
        extractor: MediaExtractorProtocol,
        go2_pipeline: GO2Pipeline,
        go3_pipeline: GO3Pipeline,
        session_repo: SessionRepositoryProtocol,
        debug_saver: DebugSaverProtocol | None = None,
    ) -> None:
        """Inject all orchestration dependencies. debug_saver defaults to NullDebugSaver."""
        self._extractor = extractor
        self._go2 = go2_pipeline
        self._go3 = go3_pipeline
        self._session_repo = session_repo
        self._debug_saver: DebugSaverProtocol = debug_saver if debug_saver is not None else NullDebugSaver()

    async def run(
        self,
        upload_bytes: bytes,
        source_filename: str,
        passage_id: str,
        learner_id: str,
    ) -> AssessmentResult:
        """
        Full pipeline: write upload → extract → GO2+GO3 in parallel → consolidate → debug save → DB insert.
        Returns AssessmentResult with db_save_failed=True if the session INSERT fails.
        Raises HTTPException(500) with code EXTRACTION_FAILED / ANALYSIS_FAILED / CONSOLIDATION_FAILED.
        """
        temp_dir = tempfile.mkdtemp()
        try:
            return await self._execute(
                upload_bytes, source_filename, passage_id, learner_id, temp_dir
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def _execute(
        self,
        upload_bytes: bytes,
        source_filename: str,
        passage_id: str,
        learner_id: str,
        temp_dir: str,
    ) -> AssessmentResult:
        """Inner pipeline logic — runs inside the temp_dir try/finally."""
        ext = os.path.splitext(source_filename)[-1] or ".webm"
        source_path = os.path.join(temp_dir, f"upload{ext}")
        with open(source_path, "wb") as f:
            f.write(upload_bytes)

        # Extract WAV + MP4
        try:
            extraction = await asyncio.to_thread(
                self._extractor.extract, source_path, temp_dir
            )
        except RuntimeError as exc:
            logger.exception("Media extraction failed for %s", source_filename)
            raise HTTPException(
                status_code=500,
                detail={"error": str(exc), "code": "EXTRACTION_FAILED"},
            ) from exc

        # Run GO2 + GO3 in parallel (both are blocking — run in thread pool)
        try:
            go2_result, go3_result = await asyncio.gather(
                asyncio.to_thread(self._go2.run, extraction["wav_path"], passage_id),
                asyncio.to_thread(self._go3.run, extraction["mp4_path"], extraction["wav_path"]),
            )
        except Exception as exc:
            logger.exception("GO2/GO3 analysis failed for passage=%s", passage_id)
            raise HTTPException(
                status_code=500,
                detail={"error": str(exc), "code": "ANALYSIS_FAILED"},
            ) from exc

        # Merge + validate
        try:
            result = ResultConsolidator.merge(dict(go2_result), dict(go3_result))
        except ValueError as exc:
            logger.exception(
                "Result consolidation failed go2_keys=%s go3_keys=%s",
                sorted(go2_result.keys()),
                sorted(go3_result.keys()),
            )
            raise HTTPException(
                status_code=500,
                detail={"error": str(exc), "code": "CONSOLIDATION_FAILED"},
            ) from exc

        # Save debug artifacts — non-fatal
        try:
            self._debug_saver.save(extraction["wav_path"], result, passage_id, learner_id)
        except Exception:
            logger.warning("debug artifact save failed — non-fatal", exc_info=True)

        # Skip DB insert when no learner identity is available
        if not learner_id.strip():
            logger.info(
                "analyze ok passage=%s wpm=%.1f pct=%.1f level=%s db_save_failed=skipped",
                passage_id,
                result.wpm,
                result.word_recognition_pct,
                result.reading_level,
            )
            return result

        # Persist session — failure is non-fatal; learner still gets their results
        db_save_failed = False
        record = SessionRecord(
            learner_id=learner_id,
            passage_id=passage_id,
            wpm=result.wpm,
            word_recognition_pct=result.word_recognition_pct,
            reading_level=result.reading_level,
            correct=result.correct,
            mispronunciation=result.mispronunciation,
            substitution=result.substitution,
            omission=result.omission,
            insertion=result.insertion,
            repetition=result.repetition,
            refusal_to_pronounce=result.refusal_to_pronounce,
            finger_pointing=result.finger_pointing,
            loss_of_place=result.loss_of_place,
            monotone_reading=result.monotone_reading,
            word_by_word_reading=result.word_by_word_reading,
            inaudible_reading=result.inaudible_reading,
        )
        try:
            await asyncio.to_thread(self._session_repo.insert, record)
        except Exception:
            logger.exception(
                "Session insert failed for learner=%s passage=%s",
                learner_id,
                passage_id,
            )
            db_save_failed = True

        logger.info(
            "analyze ok passage=%s wpm=%.1f pct=%.1f level=%s db_save_failed=%s",
            passage_id,
            result.wpm,
            result.word_recognition_pct,
            result.reading_level,
            db_save_failed,
        )
        return result.model_copy(update={"db_save_failed": db_save_failed})
