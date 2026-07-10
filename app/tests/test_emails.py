"""Tests for the email endpoints and the send_email service."""
from unittest.mock import AsyncMock

import pytest

from app.core.settings import get_settings
from app.services.email import send_email

WELCOME_PATH = "/emails/welcome"
PAYLOAD = {"record": {"email": "ada@example.com", "display_name": "Ada"}}


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Settings are lru_cached — reset around every test so env changes apply."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_welcome_refused_when_no_secret_configured(async_client, monkeypatch):
    monkeypatch.setenv("EMAIL_WEBHOOK_SECRET", "")

    response = await async_client.post(
        WELCOME_PATH, json=PAYLOAD, headers={"X-Webhook-Secret": "anything"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_welcome_refuses_wrong_secret(async_client, monkeypatch):
    monkeypatch.setenv("EMAIL_WEBHOOK_SECRET", "test-secret")

    response = await async_client.post(
        WELCOME_PATH, json=PAYLOAD, headers={"X-Webhook-Secret": "wrong"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_welcome_skips_sending_while_email_disabled(async_client, monkeypatch):
    monkeypatch.setenv("EMAIL_WEBHOOK_SECRET", "test-secret")
    monkeypatch.setenv("EMAIL_ENABLED", "false")

    response = await async_client.post(
        WELCOME_PATH, json=PAYLOAD, headers={"X-Webhook-Secret": "test-secret"}
    )

    assert response.status_code == 200
    assert response.json() == {"sent": False}


@pytest.mark.asyncio
async def test_welcome_sends_when_enabled(async_client, monkeypatch, mocker):
    monkeypatch.setenv("EMAIL_WEBHOOK_SECRET", "test-secret")
    send = mocker.patch(
        "app.routes.email_router.send_email", new=AsyncMock(return_value=True)
    )

    response = await async_client.post(
        WELCOME_PATH, json=PAYLOAD, headers={"X-Webhook-Secret": "test-secret"}
    )

    assert response.status_code == 200
    assert response.json() == {"sent": True}
    send.assert_awaited_once()
    kwargs = send.await_args.kwargs
    assert kwargs["to"] == "ada@example.com"
    assert "Ada" in kwargs["html"]


@pytest.mark.asyncio
async def test_send_email_returns_false_while_disabled(monkeypatch):
    monkeypatch.setenv("EMAIL_ENABLED", "false")

    assert await send_email("ada@example.com", "Hello", "<p>Hi</p>") is False


@pytest.mark.asyncio
async def test_send_email_requires_key_and_sender(monkeypatch):
    monkeypatch.setenv("EMAIL_ENABLED", "true")
    monkeypatch.setenv("RESEND_API_KEY", "")
    monkeypatch.setenv("EMAIL_FROM", "")

    assert await send_email("ada@example.com", "Hello", "<p>Hi</p>") is False
