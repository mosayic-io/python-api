from types import SimpleNamespace

import pytest

from app.core.auth import get_current_user
from app.main import app as fastapi_app


@pytest.mark.asyncio
async def test_public_route(async_client):
    response = await async_client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Python API!"}


@pytest.mark.asyncio
async def test_protected_route_requires_auth(async_client):
    response = await async_client.get("/protected")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_auth(async_client):
    async def override_current_user():
        return SimpleNamespace(id="123")

    fastapi_app.dependency_overrides[get_current_user] = override_current_user

    response = await async_client.get("/protected")

    assert response.status_code == 200
    assert response.json() == {"message": "You are authenticated!", "user_id": "123"}
