"""
Account deletion through the API: a thin adapter over the database function.

`delete_own_account()` in supabase/migrations/ is the single implementation.
This calls it as the caller, so the API and the app's
`supabase.rpc('delete_own_account')` can never drift apart.
"""
from fastapi import HTTPException, status

from app.core.auth import Caller
from app.core.logger import get_logger
from app.core.supabase_auth_client import AccountDeletionFailed, AuthUnavailable, SupabaseAuth

logger = get_logger(__name__)


async def delete_account(auth: SupabaseAuth, caller: Caller) -> dict:
    """Delete the caller's own account. Returns `{"deleted_user_id": <id>}`."""
    # The details go to the logs, not to the caller: Supabase's error text
    # can describe the project's internals.
    try:
        await auth.delete_own_account(caller.token)
    except AuthUnavailable:
        logger.exception("Could not reach Supabase to delete user %s", caller.user.id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )
    except AccountDeletionFailed:
        logger.exception("Failed to delete user %s", caller.user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )
    return {"deleted_user_id": caller.user.id}
