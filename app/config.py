from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Reads app config from .env — API key, WhisperX, Supabase, CORS origins."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    API_KEY: str
    WHISPERX_MODEL: str = "large-v3"
    WHISPERX_DEVICE: str = "cpu"

    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    """Returns cached Settings singleton — .env read once."""
    return Settings()  # type: ignore[call-arg]
