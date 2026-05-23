import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.dependencies import get_analysis_orchestrator
from app.models.assessment import AssessmentResult
from app.models.cv_detector import CVFlags
from app.models.media_extractor import ExtractionResult
from app.models.miscue import MiscueCounts
from app.models.passage import PassageRecord
from app.models.prosody_detector import ProsodyFlags
from app.models.scoring import ScoringResult
from app.models.session import SessionRecord
from app.models.transcription import WordSegment
from app.main import _pipeline_error_handler
from app.routers.analyze import AnalyzeController
from app.routers.health import HealthController
from app.services.analysis_orchestrator import AnalysisOrchestrator
from app.services.go2.pipeline import GO2Pipeline
from app.services.go3.pipeline import GO3Pipeline


# ---------------------------------------------------------------------------
# Fake implementations
# ---------------------------------------------------------------------------

class FakeMediaExtractor:
    """Writes empty files so the orchestrator's cleanup path works."""

    def extract(self, source_path: str, out_dir: str) -> ExtractionResult:
        """Create empty wav/mp4 placeholders and return their paths."""
        wav = os.path.join(out_dir, "audio.wav")
        mp4 = os.path.join(out_dir, "video.mp4")
        open(wav, "wb").close()  # noqa: WPS515
        open(mp4, "wb").close()  # noqa: WPS515
        return ExtractionResult(wav_path=wav, mp4_path=mp4)


class FakeMediaExtractorThatFails:
    """Always raises RuntimeError to simulate ffmpeg failure."""

    def extract(self, source_path: str, out_dir: str) -> ExtractionResult:
        """Simulate ffmpeg failure."""
        raise RuntimeError("FFmpeg extraction failed: fake error")


class FakeTranscriber:
    """Returns two fixed WordSegments."""

    def transcribe(self, wav_path: str, passage_text: str) -> list[WordSegment]:
        """Return a minimal fixed transcript."""
        return [
            WordSegment(word="the", start=0.0, end=0.5, score=0.95),
            WordSegment(word="cat", start=0.5, end=1.0, score=0.95),
        ]


class FakeMiscueClassifier:
    """Returns all-correct MiscueCounts."""

    def classify(self, transcript_words: list[WordSegment], passage_text: str) -> MiscueCounts:
        """Return zero-error miscue counts."""
        return MiscueCounts(
            correct=2, mispronunciation=0, substitution=0,
            omission=0, insertion=0, repetition=0, refusal_to_pronounce=0,
        )


class FakeScoringEngine:
    """Returns a fixed ScoringResult."""

    def score(
        self,
        transcript_words: list[WordSegment],
        miscue_counts: MiscueCounts,
        total_passage_words: int,
    ) -> ScoringResult:
        """Return fixed 80 WPM / Independent result."""
        return ScoringResult(wpm=80.0, word_recognition_pct=100.0, reading_level="Independent")


class FakePassageRepository:
    """Returns passage for p001; raises ValueError for unknown IDs."""

    def fetch(self, passage_id: str) -> PassageRecord:
        """Return a canned passage for p001."""
        if passage_id == "p001":
            return PassageRecord(text="the cat", word_count=2)
        raise ValueError(f"Passage not found: {passage_id}")


class FakeCVDetector:
    """Returns all-False CV flags."""

    def detect(self, video_path: str) -> CVFlags:
        """Return no behavioral flags detected."""
        return CVFlags(finger_pointing=False, loss_of_place=False)


class FakeProsodyDetector:
    """Returns all-False prosody flags."""

    def detect(self, wav_path: str) -> ProsodyFlags:
        """Return no prosody flags detected."""
        return ProsodyFlags(inaudible_reading=False, monotone_reading=False, word_by_word_reading=False)


class FakeSessionRepository:
    """Records the last inserted SessionRecord for assertion in tests."""

    def __init__(self) -> None:
        """Initialise with no recorded insert."""
        self.last_inserted: SessionRecord | None = None

    def insert(self, record: SessionRecord) -> None:
        """Store the record for later assertion."""
        self.last_inserted = record


class FakeSessionRepositoryThatFails:
    """Always raises to simulate a DB write error."""

    def insert(self, record: SessionRecord) -> None:
        """Raise unconditionally."""
        raise Exception("DB write error")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_orchestrator(
    extractor: FakeMediaExtractor | FakeMediaExtractorThatFails | None = None,
    session_repo: FakeSessionRepository | FakeSessionRepositoryThatFails | None = None,
) -> AnalysisOrchestrator:
    """Build an AnalysisOrchestrator wired with all fake dependencies."""
    return AnalysisOrchestrator(
        extractor=extractor or FakeMediaExtractor(),
        go2_pipeline=GO2Pipeline(
            transcriber=FakeTranscriber(),
            classifier=FakeMiscueClassifier(),
            scorer=FakeScoringEngine(),
            passage_repo=FakePassageRepository(),
        ),
        go3_pipeline=GO3Pipeline(
            cv_detector=FakeCVDetector(),
            prosody_detector=FakeProsodyDetector(),
        ),
        session_repo=session_repo or FakeSessionRepository(),
    )


def _make_client(orchestrator: AnalysisOrchestrator) -> TestClient:
    """Build a TestClient with a null lifespan and the given orchestrator injected."""

    @asynccontextmanager
    async def null_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield

    test_app = FastAPI(lifespan=null_lifespan)
    test_app.add_exception_handler(HTTPException, _pipeline_error_handler)  # type: ignore[arg-type]
    test_app.include_router(AnalyzeController().router)
    test_app.include_router(HealthController().router)
    test_app.dependency_overrides[get_analysis_orchestrator] = lambda: orchestrator
    return TestClient(test_app)


def _post(
    client: TestClient,
    passage_id: str = "p001",
    learner_id: str = "",
    api_key: str = "test-api-key",
) -> Any:
    """POST to /analyze with a fake webm file."""
    data: dict[str, str] = {"passage_id": passage_id}
    if learner_id:
        data["learner_id"] = learner_id
    return client.post(
        "/analyze",
        headers={"X-API-Key": api_key},
        files={"file": ("recording.webm", b"fake-bytes", "video/webm")},
        data=data,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_session_repo() -> FakeSessionRepository:
    """Fresh FakeSessionRepository per test."""
    return FakeSessionRepository()


@pytest.fixture
def client(fake_session_repo: FakeSessionRepository) -> TestClient:
    """TestClient wired with all fakes."""
    return _make_client(_make_orchestrator(session_repo=fake_session_repo))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_valid_request_returns_200_with_all_fields(client: TestClient) -> None:
    """Happy path — 200, all 16 AssessmentResult fields, db_save_failed=False."""
    resp = _post(client)
    assert resp.status_code == 200
    body: dict[str, Any] = resp.json()
    result = AssessmentResult(**body)
    assert result.wpm == 80.0
    assert result.reading_level == "Independent"
    assert result.db_save_failed is False
    assert len(body) == 16


def test_invalid_api_key_returns_401() -> None:
    """Wrong X-API-Key → 401."""
    c = _make_client(_make_orchestrator())
    resp = _post(c, api_key="wrong-key")
    assert resp.status_code == 401

def test_missing_passage_id_returns_422(client: TestClient) -> None:
    """No passage_id form field → 422 FastAPI validation error."""
    resp = client.post(
        "/analyze",
        headers={"X-API-Key": "test-api-key"},
        files={"file": ("r.webm", b"x", "video/webm")},
    )
    assert resp.status_code == 422


def test_ffmpeg_failure_returns_500_pipeline_failed() -> None:
    """ffmpeg failure → 500 with code=PIPELINE_FAILED."""
    c = _make_client(_make_orchestrator(extractor=FakeMediaExtractorThatFails()))
    resp = _post(c)
    assert resp.status_code == 500
    assert resp.json()["code"] == "PIPELINE_FAILED"

def test_db_failure_returns_200_with_db_save_failed_true() -> None:
    """DB insert failure → still 200 but db_save_failed=True so frontend can retry."""
    c = _make_client(_make_orchestrator(session_repo=FakeSessionRepositoryThatFails()))
    resp = _post(c, learner_id="550e8400-e29b-41d4-a716-446655440000")
    assert resp.status_code == 200
    assert resp.json()["db_save_failed"] is True

def test_empty_learner_id_skips_db_insert(
    client: TestClient, fake_session_repo: FakeSessionRepository
) -> None:
    """No learner_id → insert skipped, last_inserted stays None."""
    _post(client, learner_id="")
    assert fake_session_repo.last_inserted is None


def test_learner_id_passed_through_to_session_record(
    client: TestClient, fake_session_repo: FakeSessionRepository
) -> None:
    """Provided learner_id flows through to the SessionRecord."""
    _post(client, learner_id="550e8400-e29b-41d4-a716-446655440000")
    assert fake_session_repo.last_inserted is not None
    assert fake_session_repo.last_inserted["learner_id"] == "550e8400-e29b-41d4-a716-446655440000"


def test_webm_and_mp4_both_accepted(client: TestClient) -> None:
    """Both .webm and .mp4 uploads return 200."""
    for fname, mime in [("rec.webm", "video/webm"), ("rec.mp4", "video/mp4")]:
        resp = client.post(
            "/analyze",
            headers={"X-API-Key": "test-api-key"},
            files={"file": (fname, b"fake", mime)},
            data={"passage_id": "p001"},
        )
        assert resp.status_code == 200, f"Failed for {fname}"
