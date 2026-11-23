"""Tests for the email endpoints and the email service.

Resend is played by an httpx.MockTransport set on the service's `transport`
seam, so no test reaches the network.
"""
import json
from unittest.mock import AsyncMock

import httpx
import pytest

from app.core.settings import get_settings
from app.services import email as email_service
from app.services.email import RESEND_API_URL, send_email, send_welcome_email

WELCOME_PATH = "/emails/welcome"
PAYLOAD = {"record": {"email": "ada@example.com", "display_name": "Ada"}}


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Settings are lru_cached — reset around every test so env changes apply."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def setenv(monkeypatch):
    """Set an environment variable and drop the cached settings, so the next
    get_settings() (the webhook check, send_email) reads it."""
    def set_variable(name: str, value: str) -> None:
        monkeypatch.setenv(name, value)
        get_settings.cache_clear()
    return set_variable


class FakeResend:
    """Records each request and answers with `response` (or raises `error`)."""

    def __init__(self):
        self.requests: list[httpx.Request] = []
        self.response = httpx.Response(200, json={"id": "email-1"})
        self.error: Exception | None = None

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.response


@pytest.fixture
def resend(monkeypatch) -> FakeResend:
    fake = FakeResend()
    monkeypatch.setattr(email_service, "transport", httpx.MockTransport(fake.handle))
    return fake


@pytest.fixture
def email_on(setenv):
    setenv("EMAIL_ENABLED", "true")
    setenv("RESEND_API_KEY", "re_test")
    setenv("EMAIL_FROM", "App <info@app.test>")


# --- POST /emails/welcome ---------------------------------------------------

@pytest.mark.asyncio
async def test_welcome_refused_when_no_secret_configured(async_client, setenv):
    setenv("EMAIL_WEBHOOK_SECRET", "")

    response = await async_client.post(
        WELCOME_PATH, json=PAYLOAD, headers={"X-Webhook-Secret": "anything"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_welcome_refuses_wrong_secret(async_client, setenv):
    setenv("EMAIL_WEBHOOK_SECRET", "test-secret")

    response = await async_client.post(
        WELCOME_PATH, json=PAYLOAD, headers={"X-Webhook-Secret": "wrong"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid webhook secret"}


@pytest.mark.asyncio
async def test_welcome_refuses_missing_header(async_client, setenv):
    setenv("EMAIL_WEBHOOK_SECRET", "test-secret")

    response = await async_client.post(WELCOME_PATH, json=PAYLOAD)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_welcome_skips_sending_while_email_disabled(async_client, setenv):
    setenv("EMAIL_WEBHOOK_SECRET", "test-secret")
    setenv("EMAIL_ENABLED", "false")

    response = await async_client.post(
        WELCOME_PATH, json=PAYLOAD, headers={"X-Webhook-Secret": "test-secret"}
    )

    assert response.status_code == 200
    assert response.json() == {"sent": False}


@pytest.mark.asyncio
async def test_welcome_sends_when_enabled(async_client, setenv, email_on, resend):
    setenv("EMAIL_WEBHOOK_SECRET", "test-secret")

    response = await async_client.post(
        WELCOME_PATH, json=PAYLOAD, headers={"X-Webhook-Secret": "test-secret"}
    )

    assert response.status_code == 200
    assert response.json() == {"sent": True}
    sent = json.loads(resend.requests[0].content)
    assert sent["to"] == ["ada@example.com"]
    assert "Ada" in sent["html"]


@pytest.mark.asyncio
async def test_welcome_without_email_reports_why(async_client, setenv):
    setenv("EMAIL_WEBHOOK_SECRET", "test-secret")

    response = await async_client.post(
        WELCOME_PATH, json={"record": {"display_name": "Ada"}}, headers={"X-Webhook-Secret": "test-secret"}
    )

    assert response.status_code == 200
    assert response.json() == {"sent": False, "reason": "user has no email address"}


# --- send_welcome_email() -----------------------------------------------------

@pytest.mark.asyncio
async def test_send_welcome_email_skips_users_without_email(mocker):
    send = mocker.patch.object(email_service, "send_email", new=AsyncMock(return_value=True))

    assert await send_welcome_email(None, "Ada") == {"sent": False, "reason": "user has no email address"}
    assert await send_welcome_email("", "Ada") == {"sent": False, "reason": "user has no email address"}
    send.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_welcome_email_greets_by_name(email_on, resend):
    assert await send_welcome_email("ada@example.com", "Ada") == {"sent": True}

    sent = json.loads(resend.requests[0].content)
    assert sent["subject"] == email_service.WELCOME_SUBJECT
    assert sent["html"] == email_service.WELCOME_HTML.format(name="Ada")


@pytest.mark.asyncio
async def test_send_welcome_email_falls_back_to_there(email_on, resend):
    await send_welcome_email("ada@example.com", None)

    sent = json.loads(resend.requests[0].content)
    assert sent["html"].startswith("<p>Hi there,</p>")


@pytest.mark.asyncio
async def test_send_welcome_email_reports_a_failed_send(email_on, resend):
    resend.response = httpx.Response(500)

    assert await send_welcome_email("ada@example.com", "Ada") == {"sent": False}


# --- send_email() -------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_email_returns_false_while_disabled(setenv, resend):
    setenv("EMAIL_ENABLED", "false")

    assert await send_email("ada@example.com", "Hello", "<p>Hi</p>") is False
    assert resend.requests == []


@pytest.mark.asyncio
async def test_send_email_requires_key_and_sender(setenv, resend):
    setenv("EMAIL_ENABLED", "true")
    setenv("RESEND_API_KEY", "")
    setenv("EMAIL_FROM", "")

    assert await send_email("ada@example.com", "Hello", "<p>Hi</p>") is False
    assert resend.requests == []


@pytest.mark.asyncio
async def test_send_email_sends_the_exact_request_resend_expects(email_on, resend):
    assert await send_email("ada@example.com", "Hello", "<p>Hi</p>") is True

    assert len(resend.requests) == 1
    request = resend.requests[0]
    assert request.method == "POST"
    assert str(request.url) == RESEND_API_URL
    assert request.headers["Authorization"] == "Bearer re_test"
    assert json.loads(request.content) == {
        "from": "App <info@app.test>",
        "to": ["ada@example.com"],
        "subject": "Hello",
        "html": "<p>Hi</p>",
    }


@pytest.mark.parametrize("status_code", [400, 403, 422, 429, 500, 503])
@pytest.mark.asyncio
async def test_send_email_returns_false_when_resend_rejects(email_on, resend, status_code):
    resend.response = httpx.Response(status_code, json={"message": "nope"})

    assert await send_email("ada@example.com", "Hello", "<p>Hi</p>") is False


@pytest.mark.parametrize(
    "error",
    [httpx.ConnectError("refused"), httpx.ReadTimeout("slow")],
    ids=["connect-error", "timeout"],
)
@pytest.mark.asyncio
async def test_send_email_returns_false_when_resend_unreachable(email_on, resend, error):
    resend.error = error

    assert await send_email("ada@example.com", "Hello", "<p>Hi</p>") is False
    assert len(resend.requests) == 1
