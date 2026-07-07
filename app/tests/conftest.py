"""Core test configuration and shared fixtures."""
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.main import app as fastapi_app


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
