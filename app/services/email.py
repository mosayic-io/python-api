"""
Outgoing email via Resend (https://resend.com).

send_email() is best-effort: it returns a bool and never raises, so features
that send email can await it and move on. Nothing is sent unless
EMAIL_ENABLED=true — keep it false in development, where the email is logged
instead of sent, and turn it on in production once RESEND_API_KEY and
EMAIL_FROM are configured.
"""
import httpx

from app.core.logger import get_logger
from app.core.settings import get_settings

logger = get_logger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


async def send_email(to: str, subject: str, html: str) -> bool:
    """Send one email through Resend. Returns True if Resend accepted it."""
    settings = get_settings()

    if not settings.email_enabled:
        logger.info("EMAIL_ENABLED is false — skipped sending %r to %s", subject, to)
        return False

    if not settings.resend_api_key or not settings.email_from:
        logger.error("EMAIL_ENABLED is true but RESEND_API_KEY or EMAIL_FROM is not set")
        return False

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                RESEND_API_URL,
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={
                    "from": settings.email_from,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
            )
    except httpx.HTTPError as error:
        logger.error("Could not reach Resend: %s", error)
        return False

    if response.status_code >= 400:
        logger.error("Resend rejected the email (%s): %s", response.status_code, response.text)
        return False

    logger.info("Sent %r to %s", subject, to)
    return True
