"""
Email endpoints.

POST /emails/welcome is designed to be called by a Supabase database webhook
whenever a row is inserted into public.users (which the auth trigger does for
every new sign-up, whatever the provider). Configure the webhook to send an
X-Webhook-Secret header and set the same value in EMAIL_WEBHOOK_SECRET —
requests without it are refused.

If email confirmation is switched on (supabase/config.toml
`enable_confirmations`, and the hosted project's "Confirm email" toggle),
an INSERT webhook fires before the address is confirmed. Hook it to the
confirmation instead: a trigger on auth.users for the moment
email_confirmed_at is first set, posting the same `{record: {email,
display_name}}` shape — never the auth.users row itself.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.settings import get_settings
from app.core.webhooks import verified_webhook
from app.services import email

router = APIRouter(prefix="/emails", tags=["Emails"])


class UserRecord(BaseModel):
    email: str | None = None
    display_name: str | None = None


class UserCreatedPayload(BaseModel):
    """The relevant slice of a Supabase database webhook INSERT payload."""
    record: UserRecord


@router.post(
    "/welcome",
    dependencies=[Depends(verified_webhook(lambda: get_settings().email_webhook_secret))],
)
async def send_welcome_email(payload: UserCreatedPayload) -> dict:
    return await email.send_welcome_email(payload.record.email, payload.record.display_name)
