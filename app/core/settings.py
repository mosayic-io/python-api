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

    # Outgoing email via Resend (app/services/email.py). Keep EMAIL_ENABLED
    # false in development so local runs never email real people. The welcome
    # endpoint refuses requests unless EMAIL_WEBHOOK_SECRET matches the
    # X-Webhook-Secret header sent by the Supabase database webhook.
    email_enabled: bool = False
    resend_api_key: str = ""
    email_from: str = ""
    email_webhook_secret: str = ""


@lru_cache()
def get_settings():
    """
    Get application settings instance.

    Uses lru_cache to ensure only one Settings instance is created
    and reused across the application lifecycle.
    """
    return Settings()
