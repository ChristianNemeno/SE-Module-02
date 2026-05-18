from app.models.transcription import TranscriberProtocol
from app.services.go2.transcriber import get_transcriber_instance


def get_transcriber() -> TranscriberProtocol:
    """FastAPI dependency provider for TranscriberProtocol — returns the singleton."""
    return get_transcriber_instance()
