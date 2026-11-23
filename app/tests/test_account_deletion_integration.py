"""Parity check: DELETE /auth/users/me against the LOCAL Supabase stack.

It proves the endpoint really runs `delete_own_account()` as the caller:
the auth user and the public.users row are both gone afterwards.

A plain `uv run pytest` deselects it (addopts in pyproject.toml). Run it with
`uv run pytest -m integration` after `npx supabase start`. Even then it skips
itself unless SUPABASE_URL points at this machine (127.0.0.1 or localhost)
and the stack answers, so it can never touch a hosted project. Any local
stack on that port answers, another project's included: check
`npx supabase status` first.
"""
import uuid
from urllib.parse import urlparse

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.settings import get_settings
from app.factory import create_app

pytestmark = pytest.mark.integration

LOCAL_HOSTS = {"127.0.0.1", "localhost"}


def local_stack_or_skip() -> tuple[str, str]:
    settings = get_settings()
    url = settings.supabase_url.rstrip("/")
    if urlparse(url).hostname not in LOCAL_HOSTS:
        pytest.skip("SUPABASE_URL is not a 127.0.0.1/localhost URL: the local stack only")
    if not settings.supabase_secret_key:
        pytest.skip("SUPABASE_SECRET_KEY is not set")
    try:
        health = httpx.get(
            f"{url}/auth/v1/health",
            headers={"apikey": settings.supabase_secret_key},
            timeout=2,
        )
    except httpx.HTTPError:
        pytest.skip("the local Supabase stack is not running (npx supabase start)")
    if health.status_code != 200:
        pytest.skip(f"the local Supabase stack answered {health.status_code}")
    return url, settings.supabase_secret_key


@pytest.mark.asyncio
async def test_delete_endpoint_removes_auth_user_and_profile_row():
    url, secret_key = local_stack_or_skip()
    service = {"apikey": secret_key, "Authorization": f"Bearer {secret_key}"}
    email = f"deletion-parity-{uuid.uuid4().hex[:12]}@example.com"
    password = f"pw-{uuid.uuid4().hex}"

    async with httpx.AsyncClient(base_url=url, timeout=10) as supabase:
        created = await supabase.post(
            "/auth/v1/admin/users",
            headers=service,
            json={"email": email, "password": password, "email_confirm": True},
        )
        assert created.status_code == 200, created.text
        user_id = created.json()["id"]

        try:
            signed_in = await supabase.post(
                "/auth/v1/token",
                params={"grant_type": "password"},
                headers={"apikey": secret_key},
                json={"email": email, "password": password},
            )
            assert signed_in.status_code == 200, signed_in.text
            token = signed_in.json()["access_token"]

            profile = await supabase.get(f"/rest/v1/users?id=eq.{user_id}&select=id", headers=service)
            assert profile.json() == [{"id": user_id}]

            app = create_app()
            async with app.router.lifespan_context(app):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as api:
                    response = await api.delete(
                        "/auth/users/me", headers={"Authorization": f"Bearer {token}"}
                    )

            assert response.status_code == 200, response.text
            assert response.json() == {"deleted_user_id": user_id}

            auth_user = await supabase.get(f"/auth/v1/admin/users/{user_id}", headers=service)
            assert auth_user.status_code == 404
            profile = await supabase.get(f"/rest/v1/users?id=eq.{user_id}&select=id", headers=service)
            assert profile.json() == []
        finally:
            # Leave no test user behind if an assertion failed before deletion
            await supabase.delete(f"/auth/v1/admin/users/{user_id}", headers=service)
