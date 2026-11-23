"""Core test configuration and shared fixtures."""
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.auth import get_auth
from app.factory import create_app
from app.tests.fakes import FakeSupabaseAuth


@pytest.fixture
def fake_auth() -> FakeSupabaseAuth:
    """The in-memory Supabase Auth the test's app uses."""
    return FakeSupabaseAuth()


@pytest.fixture
def app(fake_auth: FakeSupabaseAuth) -> FastAPI:
    """A fresh FastAPI app for each test, with Supabase Auth faked."""
    app = create_app()
    app.dependency_overrides[get_auth] = lambda: fake_auth
    return app


@pytest_asyncio.fixture
async def async_client(app: FastAPI):
    """HTTP client for FastAPI endpoint testing"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost:8080") as client:
        yield client
