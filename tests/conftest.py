"""Core test configuration and shared fixtures."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.main import app as fastapi_app

# Import fixture modules to make them available
pytest_plugins = [
    "tests.fixtures.auth_fixtures",
    "tests.fixtures.database_fixtures",
]


@pytest.fixture(scope="session")
def event_loop():
    """Session-wide event loop for async tests"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def app() -> FastAPI:
    """Fresh FastAPI app instance with test config"""
    fastapi_app.dependency_overrides.clear()
    return fastapi_app


@pytest_asyncio.fixture(scope="function")
async def async_client(app: FastAPI):
    """HTTP client for FastAPI endpoint testing"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost:8080") as client:
        yield client


@pytest.fixture(autouse=True)
def cleanup_dependency_overrides():
    """Ensure dependency overrides are cleaned up after each test"""
    yield
    fastapi_app.dependency_overrides.clear()