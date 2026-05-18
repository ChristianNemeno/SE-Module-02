from app.models.scoring import ScoringEngineProtocol
from app.models.transcription import TranscriberProtocol
from app.services.go2.scoring_engine import ScoringEngine
from app.services.go2.transcriber import get_transcriber_instance


def get_transcriber() -> TranscriberProtocol:
    """FastAPI dependency provider for TranscriberProtocol — returns the singleton."""
    return get_transcriber_instance()


def get_scoring_engine() -> ScoringEngineProtocol:
    """FastAPI dependency provider for ScoringEngineProtocol — cheap, instantiated per call."""
    return ScoringEngine()
