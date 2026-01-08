from unittest.mock import AsyncMock

import pytest

from app.core.auth import get_current_user
from app.main import app as fastapi_app

SUPABASE_CLIENT_PATH = "app.core.supabase_client.SupabaseClient"


@pytest.mark.asyncio
async def test_delete_user(async_client, mocker):
    supabase = mocker.Mock()
    supabase.auth.admin.delete_user = AsyncMock(return_value=None)
    mocker.patch(f"{SUPABASE_CLIENT_PATH}.get_client", new=AsyncMock(return_value=supabase))

    async def override_current_user():
        return object()

    fastapi_app.dependency_overrides[get_current_user] = override_current_user
    try:
        response = await async_client.delete("/auth/users/123")
    finally:
        fastapi_app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"deleted_user_id": "123"}
    supabase.auth.admin.delete_user.assert_awaited_once_with("123")
