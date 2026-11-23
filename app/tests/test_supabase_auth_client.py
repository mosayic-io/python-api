"""Tests for SupabaseAuth itself: how Supabase's answers become its error
modes, and the exact requests it sends. httpx.MockTransport plays Supabase."""
import httpx
import pytest

from app.core.supabase_auth_client import (
    AccountDeletionFailed,
    AuthUnavailable,
    InvalidToken,
    SupabaseAuth,
)

SUPABASE_URL = "http://supabase.test"
SECRET_KEY = "sb_secret_test"
USER_JSON = {
    "id": "123",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
}


def auth_answering(handler) -> SupabaseAuth:
    return SupabaseAuth(SUPABASE_URL, SECRET_KEY, transport=httpx.MockTransport(handler))


def answer(status_code: int, **kwargs):
    return lambda request: httpx.Response(status_code, **kwargs)


def refuse_connection(request: httpx.Request):
    raise httpx.ConnectError("connection refused", request=request)


@pytest.mark.asyncio
async def test_current_user_returns_the_user_and_sends_the_token():
    seen = []

    def handler(request: httpx.Request):
        seen.append(request)
        return httpx.Response(200, json=USER_JSON)

    user = await auth_answering(handler).current_user("user-jwt")

    assert user.id == "123"
    request = seen[0]
    assert str(request.url) == f"{SUPABASE_URL}/auth/v1/user"
    assert request.headers["Authorization"] == "Bearer user-jwt"
    assert request.headers["apikey"] == SECRET_KEY


@pytest.mark.parametrize("status_code", [400, 401, 403, 404])
@pytest.mark.asyncio
async def test_current_user_refused_token_is_invalid(status_code):
    auth = auth_answering(answer(status_code, json={"code": "bad_jwt", "msg": "invalid JWT"}))

    with pytest.raises(InvalidToken):
        await auth.current_user("expired")


@pytest.mark.parametrize("status_code", [429, 500, 502, 503, 504])
@pytest.mark.asyncio
async def test_current_user_server_trouble_is_unavailable(status_code):
    auth = auth_answering(answer(status_code, json={"msg": "upstream trouble"}))

    with pytest.raises(AuthUnavailable):
        await auth.current_user("user-jwt")


@pytest.mark.asyncio
async def test_current_user_non_json_error_page_is_unavailable():
    auth = auth_answering(answer(500, text="<html>Bad gateway</html>"))

    with pytest.raises(AuthUnavailable):
        await auth.current_user("user-jwt")


@pytest.mark.asyncio
async def test_current_user_unreachable_is_unavailable():
    with pytest.raises(AuthUnavailable):
        await auth_answering(refuse_connection).current_user("user-jwt")


@pytest.mark.asyncio
async def test_delete_own_account_calls_the_function_as_the_caller():
    seen = []

    def handler(request: httpx.Request):
        seen.append(request)
        return httpx.Response(204)

    await auth_answering(handler).delete_own_account("user-jwt")

    request = seen[0]
    assert request.method == "POST"
    assert str(request.url) == f"{SUPABASE_URL}/rest/v1/rpc/delete_own_account"
    assert request.headers["Authorization"] == "Bearer user-jwt"
    assert request.headers["apikey"] == SECRET_KEY
    assert request.content == b"{}"


@pytest.mark.parametrize("status_code", [400, 401, 403, 404])
@pytest.mark.asyncio
async def test_delete_own_account_refused_is_deletion_failed(status_code):
    auth = auth_answering(answer(status_code, json={"code": "42501", "message": "not signed in"}))

    with pytest.raises(AccountDeletionFailed):
        await auth.delete_own_account("user-jwt")


@pytest.mark.parametrize("status_code", [500, 503])
@pytest.mark.asyncio
async def test_delete_own_account_server_trouble_is_unavailable(status_code):
    with pytest.raises(AuthUnavailable):
        await auth_answering(answer(status_code)).delete_own_account("user-jwt")


@pytest.mark.asyncio
async def test_delete_own_account_unreachable_is_unavailable():
    with pytest.raises(AuthUnavailable):
        await auth_answering(refuse_connection).delete_own_account("user-jwt")


def test_building_needs_no_settings_and_no_network():
    # Blank URL and key, as in a test run or a fresh checkout without .env:
    # construction must neither fail nor call out.
    SupabaseAuth("", "")
