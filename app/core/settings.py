import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.local",
        extra='allow',
        env_file_encoding='utf-8'
    )

    # Core settings
    debug_mode: bool = False
    environment: str = "development"

    # These are loaded from .env.local or environment variables
    supabase_service_role_key: str = ""
    supabase_url: str = ""
    api_key: str = ""



@lru_cache()
def get_settings():
    """
    Get application settings instance.

    Uses lru_cache to ensure only one Settings instance is created
    and reused across the application lifecycle.
    """
    return Settings()
