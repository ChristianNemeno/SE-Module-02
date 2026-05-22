from app.models.cv_detector import CVDetectorProtocol
from app.models.scoring import ScoringEngineProtocol
from app.models.transcription import TranscriberProtocol
from app.services.go2.scoring_engine import ScoringEngine
from app.services.go2.transcriber import get_transcriber_instance
from app.services.go3.cv_detector import get_detector_instance


def get_transcriber() -> TranscriberProtocol:
    """FastAPI dependency provider for TranscriberProtocol — returns the singleton."""
    return get_transcriber_instance()


def get_scoring_engine() -> ScoringEngineProtocol:
    """FastAPI dependency provider for ScoringEngineProtocol — cheap, instantiated per call."""
    return ScoringEngine()


def get_cv_detector() -> CVDetectorProtocol:
    """FastAPI dependency provider for CVDetectorProtocol — returns the singleton."""
    return get_detector_instance()
