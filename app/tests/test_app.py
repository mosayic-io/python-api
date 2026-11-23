"""Tests for create_app(): assembly and the lifespan."""
import pytest

from app.core.settings import Settings
from app.core.supabase_auth_client import SupabaseAuth
from app.factory import create_app


@pytest.mark.asyncio
async def test_lifespan_starts_without_supabase_settings():
    # Blank URL and key: startup must neither fail nor call Supabase.
    app = create_app(Settings(_env_file=None, supabase_url="", supabase_secret_key=""))

    async with app.router.lifespan_context(app):
        assert isinstance(app.state.auth, SupabaseAuth)


def test_docs_are_off_in_production():
    app = create_app(Settings(_env_file=None, app_env="production"))

    assert app.docs_url is None and app.redoc_url is None and app.openapi_url is None


def test_docs_are_on_in_development():
    app = create_app(Settings(_env_file=None, app_env="development"))

    assert app.docs_url == "/docs"
