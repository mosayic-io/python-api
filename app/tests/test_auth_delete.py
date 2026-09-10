from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.auth import get_current_user
from app.main import app as fastapi_app

SUPABASE_CLIENT_PATH = "app.core.supabase_client.SupabaseClient"


@pytest.mark.asyncio
async def test_delete_current_user(async_client, mocker):
    supabase = mocker.Mock()
    supabase.auth.admin.delete_user = AsyncMock(return_value=None)
    mocker.patch(f"{SUPABASE_CLIENT_PATH}.get_client", new=AsyncMock(return_value=supabase))

    async def override_current_user():
        return SimpleNamespace(id="123")

    fastapi_app.dependency_overrides[get_current_user] = override_current_user

    response = await async_client.delete("/auth/users/me")

    assert response.status_code == 200
    assert response.json() == {"deleted_user_id": "123"}
    supabase.auth.admin.delete_user.assert_awaited_once_with("123")


@pytest.mark.asyncio
async def test_delete_current_user_requires_auth(async_client):
    response = await async_client.delete("/auth/users/me")

    assert response.status_code == 401
