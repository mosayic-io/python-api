"""
Outgoing email via Resend (https://resend.com).

send_email() is best-effort: it returns a bool and never raises, so features
that send email can await it and move on. Nothing is sent unless
EMAIL_ENABLED=true — keep it false in development, where the email is logged
instead of sent, and turn it on in production once RESEND_API_KEY and
EMAIL_FROM are configured.

send_welcome_email() holds the welcome email's rules (who gets one, the name
it greets, the template); POST /emails/welcome is just the webhook's door to it.
"""
import httpx

from app.core.logger import get_logger
from app.core.settings import get_settings

logger = get_logger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"

# The httpx transport send_email() talks to Resend through. None is the real
# network; tests set an httpx.MockTransport here to play Resend.
transport: httpx.AsyncBaseTransport | None = None

# Personalise the welcome email for your app — or ask Claude to.
WELCOME_SUBJECT = "Welcome!"
WELCOME_HTML = (
    "<p>Hi {name},</p>"
    "<p>Thanks for signing up — we're glad you're here.</p>"
    "<p>If you have any questions, just reply to this email.</p>"
)


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
        async with httpx.AsyncClient(timeout=10, transport=transport) as client:
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


async def send_welcome_email(email: str | None, display_name: str | None) -> dict:
    """Welcome a new user. Returns the outcome, e.g. `{"sent": True}`.

    A user without an email address (a phone sign-up, say) is skipped with a
    reason; a user without a display name is greeted as "there".
    """
    if not email:
        return {"sent": False, "reason": "user has no email address"}

    name = display_name or "there"
    sent = await send_email(to=email, subject=WELCOME_SUBJECT, html=WELCOME_HTML.format(name=name))
    return {"sent": sent}
