"""
Email endpoints.

POST /emails/welcome is designed to be called by a Supabase database webhook
whenever a row is inserted into public.users (which the auth trigger does for
every new sign-up, whatever the provider). Configure the webhook to send an
X-Webhook-Secret header and set the same value in EMAIL_WEBHOOK_SECRET —
requests without it are refused.
"""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.core.settings import get_settings
from app.services.email import send_email

router = APIRouter(prefix="/emails", tags=["Emails"])

# Personalise the welcome email for your app — or ask Claude to.
WELCOME_SUBJECT = "Welcome!"
WELCOME_HTML = (
    "<p>Hi {name},</p>"
    "<p>Thanks for signing up — we're glad you're here.</p>"
    "<p>If you have any questions, just reply to this email.</p>"
)


class UserRecord(BaseModel):
    email: str | None = None
    display_name: str | None = None


class UserCreatedPayload(BaseModel):
    """The relevant slice of a Supabase database webhook INSERT payload."""
    record: UserRecord


@router.post("/welcome")
async def send_welcome_email(
    payload: UserCreatedPayload,
    x_webhook_secret: str | None = Header(default=None),
) -> dict:
    settings = get_settings()
    if not settings.email_webhook_secret or x_webhook_secret != settings.email_webhook_secret:
        raise HTTPException(status_code=401, detail="Missing or invalid webhook secret")

    if not payload.record.email:
        return {"sent": False, "reason": "user has no email address"}

    name = payload.record.display_name or "there"
    sent = await send_email(
        to=payload.record.email,
        subject=WELCOME_SUBJECT,
        html=WELCOME_HTML.format(name=name),
    )
    return {"sent": sent}
