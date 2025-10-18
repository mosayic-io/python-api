"""Authentication-related test fixtures."""
import pytest
import pytest_asyncio
from fastapi import FastAPI

from app.core.auth import get_current_user


@pytest.fixture
def test_user() -> dict:
    """Standard test user"""
    return {
        "uid": "test_user_123",
        "email": "test@example.com",
        "role": "authenticated",
        "email_verified": True
    }


@pytest.fixture
def admin_user() -> dict:
    """Admin test user"""
    return {
        "uid": "admin_123",
        "email": "admin@example.com",
        "role": "admin",
        "email_verified": True
    }


@pytest.fixture(scope="function")
def login_as_user(app: FastAPI, test_user: dict):
    """Override auth dependency to return test user"""
    app.dependency_overrides[get_current_user] = lambda: test_user
    yield test_user
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def login_as_admin(app: FastAPI, admin_user: dict):
    """Override auth dependency to return admin user"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    yield admin_user
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_login_as_user(app: FastAPI, test_user: dict):
    """Override auth dependency to return test user (async)"""
    app.dependency_overrides[get_current_user] = lambda: test_user
    yield test_user
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_login_as_admin(app: FastAPI, admin_user: dict):
    """Override auth dependency to return admin user (async)"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    yield admin_user
    app.dependency_overrides.clear()