"""
Shared-secret checks for incoming webhooks.

`verified_webhook(secret_getter)` builds a dependency that refuses a request
(401) unless its X-Webhook-Secret header matches the configured secret. Use
it on any route a webhook calls:

    @router.post("/hook", dependencies=[Depends(verified_webhook(lambda: get_settings().my_secret))])

The getter runs on every request, so the secret is read from settings at
call time, never frozen at import. A blank secret refuses everything: a
webhook endpoint is never open by accident.
"""
import hmac
from collections.abc import Callable

from fastapi import Header, HTTPException, status


def verified_webhook(secret_getter: Callable[[], str]) -> Callable:
    """A dependency that requires X-Webhook-Secret to equal `secret_getter()`."""

    async def verify(x_webhook_secret: str | None = Header(default=None)) -> None:
        secret = secret_getter()
        # compare_digest takes the same time however much of the secret matches,
        # so the header can't be guessed one character at a time.
        if not secret or not hmac.compare_digest(
            (x_webhook_secret or "").encode(), secret.encode()
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid webhook secret",
            )

    return verify
