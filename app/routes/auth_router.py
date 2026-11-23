"""Account deletion through the API: the second door to the same deletion.

Apple and Google require an in-app way to delete an account. There is one
implementation, the database function `delete_own_account()` (a migration in
`supabase/migrations/`), and two ways to reach it, with one constant in the
mobile app choosing (`ACCOUNT_DELETION` in the app's `src/lib/api.ts`):

- `supabase.rpc('delete_own_account')` from the app: works before any
  server is deployed, so it is the app's default;
- this endpoint, `DELETE /auth/users/me`: the server calls the same
  function as the signed-in caller, with their own session token, for apps
  that route it through the API (the "Deleting Users" lesson walks through it).

Both delete only the signed-in caller: the function deletes `auth.uid()`
from the session token, and nothing in the request names a user. Extend the
function, never this endpoint, when a feature needs more removed (its files
in Storage, say).
"""
from fastapi import APIRouter, Depends

from app.core.auth import Caller, get_auth, get_caller
from app.core.supabase_auth_client import SupabaseAuth
from app.services.account import delete_account

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.delete("/users/me")
async def delete_user(
    caller: Caller = Depends(get_caller),
    auth: SupabaseAuth = Depends(get_auth),
) -> dict:
    return await delete_account(auth, caller)
