from supabase import Client, create_client

from app.config import get_settings

_client: Client | None = None


def init_supabase_client() -> None:
    """Create and cache the Supabase sync client using service key. No-op if credentials are missing."""
    global _client
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        return
    _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


def get_supabase_client() -> Client | None:
    """Return the cached Supabase client, or None if not initialised."""
    return _client
