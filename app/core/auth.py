"""
The auth dependencies every protected route uses.

- `get_current_user`: the verified Supabase user. Depend on it to protect a
  route.
- `get_caller`: the verified user AND their raw session token, for the rare
  route that acts as the user against Supabase (account deletion).
- `get_auth`: the app's SupabaseAuth, built once in the lifespan. Tests
  override it with the in-memory fake in `app/tests/fakes.py`.

A bad or expired token is a 401 (sign in again). Supabase being down is a
503, so an outage never tells the mobile app its session is invalid.
"""
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase_auth.types import User

from app.core.logger import get_logger
from app.core.supabase_auth_client import AuthUnavailable, InvalidToken, SupabaseAuth

logger = get_logger(__name__)

auth_scheme = HTTPBearer()


@dataclass(frozen=True)
class Caller:
    """A verified user and the session token they called with."""
    user: User
    token: str


def get_auth(request: Request) -> SupabaseAuth:
    """The SupabaseAuth the lifespan stored on the app."""
    return request.app.state.auth


async def get_caller(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    auth: SupabaseAuth = Depends(get_auth),
) -> Caller:
    """Verify the bearer token with Supabase Auth and return who sent it."""
    token = credentials.credentials
    try:
        user = await auth.current_user(token)
    except InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    except AuthUnavailable as error:
        logger.error("Could not verify a session token: %s", error)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )
    return Caller(user=user, token=token)


async def get_current_user(caller: Caller = Depends(get_caller)) -> User:
    """Dependency to verify the JWT and return the current user."""
    return caller.user
