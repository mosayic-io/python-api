"""Tests for the auth dependencies and DELETE /auth/users/me, at the
SupabaseAuth interface (the in-memory fake in fakes.py)."""
import pytest

DELETE_PATH = "/auth/users/me"


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_protected_route_accepts_a_valid_token(async_client, fake_auth):
    token = fake_auth.sign_in("123")

    response = await async_client.get("/protected", headers=bearer(token))

    assert response.status_code == 200
    assert response.json() == {"message": "You are authenticated!", "user_id": "123"}


@pytest.mark.asyncio
async def test_invalid_token_is_401(async_client):
    response = await async_client.get("/protected", headers=bearer("expired"))

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication credentials"}


@pytest.mark.asyncio
async def test_supabase_outage_is_503_not_401(async_client, fake_auth):
    token = fake_auth.sign_in("123")
    fake_auth.unavailable = True

    response = await async_client.get("/protected", headers=bearer(token))

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication service unavailable"}


@pytest.mark.asyncio
async def test_delete_current_user(async_client, fake_auth):
    token = fake_auth.sign_in("123")

    response = await async_client.delete(DELETE_PATH, headers=bearer(token))

    assert response.status_code == 200
    assert response.json() == {"deleted_user_id": "123"}
    assert fake_auth.deleted_user_ids == ["123"]
    # The session dies with the account
    again = await async_client.get("/protected", headers=bearer(token))
    assert again.status_code == 401


@pytest.mark.asyncio
async def test_delete_current_user_requires_auth(async_client, fake_auth):
    response = await async_client.delete(DELETE_PATH)

    assert response.status_code == 401
    assert fake_auth.deleted_user_ids == []


@pytest.mark.asyncio
async def test_delete_failure_keeps_supabase_error_private(async_client, fake_auth):
    token = fake_auth.sign_in("123")
    fake_auth.refuse_deletion = True

    response = await async_client.delete(DELETE_PATH, headers=bearer(token))

    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to delete user"}


@pytest.mark.asyncio
async def test_delete_during_outage_is_503(async_client, fake_auth):
    token = fake_auth.sign_in("123")
    fake_auth.unavailable = True

    response = await async_client.delete(DELETE_PATH, headers=bearer(token))

    assert response.status_code == 503
    assert fake_auth.deleted_user_ids == []
