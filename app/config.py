from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Gi-load ang config gikan sa .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    API_KEY: str


@lru_cache
def get_settings() -> Settings:
    """Returns cached Settings instance. Singleton ra ni para dili mag-reload sa .env every request."""
    return Settings()  # type: ignore[call-arg]  # pydantic-settings reads API_KEY from env
