from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8",
    )

    # Core settings — set APP_ENV=production in deployed environments
    app_env: str = "development"

    # These are loaded from .env or environment variables
    supabase_secret_key: str = ""
    supabase_url: str = ""


@lru_cache()
def get_settings():
    """
    Get application settings instance.

    Uses lru_cache to ensure only one Settings instance is created
    and reused across the application lifecycle.
    """
    return Settings()
