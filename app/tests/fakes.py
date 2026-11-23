"""In-memory stand-ins for the app's third-party wrappers, for tests.

The `app` fixture (conftest.py) overrides `get_auth` with a FakeSupabaseAuth,
so no test reaches Supabase. Give a test a signed-in user with
`fake_auth.sign_in("user-123")`, then send its token as the bearer.
"""
from supabase_auth.types import User

from app.core.supabase_auth_client import AccountDeletionFailed, AuthUnavailable, InvalidToken


def make_user(user_id: str, email: str | None = None) -> User:
    return User(
        id=user_id,
        email=email,
        app_metadata={},
        user_metadata={},
        aud="authenticated",
        created_at="2026-01-01T00:00:00Z",
    )


class FakeSupabaseAuth:
    """Same interface and error modes as SupabaseAuth, backed by a dict."""

    def __init__(self):
        self.users_by_token: dict[str, User] = {}
        self.deleted_user_ids: list[str] = []
        # Flip these to exercise the error paths
        self.unavailable = False
        self.refuse_deletion = False

    def sign_in(self, user_id: str, email: str | None = None) -> str:
        """Register a user and return a session token for them."""
        token = f"token-for-{user_id}"
        self.users_by_token[token] = make_user(user_id, email)
        return token

    async def current_user(self, token: str) -> User:
        if self.unavailable:
            raise AuthUnavailable("fake: Supabase is down")
        user = self.users_by_token.get(token)
        if user is None:
            raise InvalidToken("fake: unknown token")
        return user

    async def delete_own_account(self, token: str) -> None:
        if self.unavailable:
            raise AuthUnavailable("fake: Supabase is down")
        if self.refuse_deletion:
            raise AccountDeletionFailed("fake: db at 10.0.0.5 refused")
        user = self.users_by_token.pop(token, None)
        if user is None:
            raise AccountDeletionFailed("fake: not signed in")
        # The token is dead with the account, like the real thing
        self.deleted_user_ids.append(user.id)

    async def aclose(self) -> None:
        pass
