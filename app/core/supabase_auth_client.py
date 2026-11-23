"""
Supabase Auth, as the API needs it: who is calling, and deleting their account.

One SupabaseAuth is built per app, in the lifespan (`app/factory.py`), and
reached through the `get_auth` dependency (`app/core/auth.py`). Building it
makes no network call, so the app starts even with SUPABASE_URL unset.

Its error modes are part of the interface:

- InvalidToken: the session token is bad, expired or for a deleted user. The
  caller should sign in again (401).
- AuthUnavailable: Supabase could not be reached, timed out, or answered with
  a server error or a rate limit. The caller's session may be fine (503).
- AccountDeletionFailed: Supabase answered, and refused the deletion (500).
  The message holds Supabase's answer, for the logs only.
"""
import httpx
from supabase_auth import AsyncGoTrueClient
from supabase_auth.errors import AuthApiError, AuthError, AuthRetryableError, AuthUnknownError
from supabase_auth.types import User

from app.core.settings import Settings

# What Supabase's own client treats as "the network, not your request":
# gateway errors plus Cloudflare's 52x family (supabase_auth.helpers).
UNAVAILABLE_STATUSES = {429, 502, 503, 504, 520, 521, 522, 523, 524, 530}


class InvalidToken(Exception):
    """The session token was refused: sign in again."""


class AuthUnavailable(Exception):
    """Supabase could not answer: try again later."""


class AccountDeletionFailed(Exception):
    """Supabase answered and the deletion did not happen."""


class SupabaseAuth:
    def __init__(
        self,
        supabase_url: str,
        secret_key: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        """`transport` is for tests: an httpx.MockTransport stands in for Supabase."""
        self._url = supabase_url.rstrip("/")
        self._secret_key = secret_key
        # One connection pool for the app. Nothing on it is per-user: each
        # request carries its caller's token in its own headers.
        self._http = httpx.AsyncClient(timeout=10, follow_redirects=True, transport=transport)
        self._gotrue = AsyncGoTrueClient(
            url=f"{self._url}/auth/v1",
            headers={"apikey": secret_key},
            http_client=self._http,
            auto_refresh_token=False,
            persist_session=False,
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupabaseAuth":
        return cls(settings.supabase_url, settings.supabase_secret_key)

    async def current_user(self, token: str) -> User:
        """The user a session token belongs to, as Supabase Auth sees it now."""
        try:
            response = await self._gotrue.get_user(jwt=token)
        except Exception as error:
            classified = _classify(error)
            if classified is error:
                raise
            raise classified from error
        if response is None or response.user is None:
            raise InvalidToken("Supabase returned no user for the token")
        return response.user

    async def delete_own_account(self, token: str) -> None:
        """Delete the token's own account by calling the database function.

        `delete_own_account()` (supabase/migrations/20260101120100_app_functions.sql)
        is the one implementation of account deletion: the app's
        `supabase.rpc('delete_own_account')` and this call run the same SQL,
        as the same signed-in user, so anything a feature adds to the
        function (storage cleanup, say) happens on both paths.

        The secret key only gets the request through the API gateway. The
        Postgres role and `auth.uid()` come from the caller's token in
        Authorization; if that ever failed to happen, `auth.uid()` would be
        null and the function refuses, so no one else's account can go.
        """
        try:
            response = await self._http.post(
                f"{self._url}/rest/v1/rpc/delete_own_account",
                headers={
                    "apikey": self._secret_key,
                    "Authorization": f"Bearer {token}",
                },
                json={},
            )
        except httpx.HTTPError as error:
            raise AuthUnavailable(f"Could not reach Supabase: {error!r}") from error

        if response.status_code in UNAVAILABLE_STATUSES or response.status_code >= 500:
            raise AuthUnavailable(f"Supabase answered {response.status_code}: {response.text}")
        if response.status_code >= 400:
            raise AccountDeletionFailed(f"Supabase answered {response.status_code}: {response.text}")

    async def aclose(self) -> None:
        await self._http.aclose()


def _classify(error: Exception) -> Exception:
    """Sort what supabase_auth raises into this module's two error modes.

    supabase_auth wraps HTTP error answers (AuthApiError, or
    AuthRetryableError for gateway errors) but lets httpx's transport errors
    (connection refused, timeouts) through unwrapped. Anything else is a bug
    here, not a verdict on the token, and is re-raised as it is.
    """
    if isinstance(error, httpx.HTTPError):
        return AuthUnavailable(f"Could not reach Supabase: {error!r}")
    if isinstance(error, AuthRetryableError):
        return AuthUnavailable(f"Supabase is unavailable: {error.message}")
    if isinstance(error, AuthApiError):
        if error.status in UNAVAILABLE_STATUSES or error.status >= 500:
            return AuthUnavailable(f"Supabase answered {error.status}: {error.message}")
        return InvalidToken(f"Supabase refused the token ({error.status}): {error.message}")
    if isinstance(error, AuthUnknownError):
        # An error answer that wasn't Supabase's JSON: an HTML error page
        # from a proxy, or a SUPABASE_URL that points somewhere else.
        return AuthUnavailable(f"Unexpected answer from Supabase: {error.message}")
    if isinstance(error, AuthError):
        return InvalidToken(f"Supabase refused the token: {error.message}")
    return error
