"""Account deletion through the API — the second of the template's two ways.

Apple and Google require an in-app way to delete an account, and this
template ships it twice, with one constant in the mobile app choosing
(`ACCOUNT_DELETION` in the app's `src/lib/api.ts`):

- the database function `delete_own_account()` (a migration in
  `supabase/migrations/`), called with `supabase.rpc` — works before any
  server is deployed, so it is the app's default;
- this endpoint, `DELETE /auth/users/me` — the same deletion done by the
  server with the service-role key, for apps that route it through the
  API (the "Deleting Users" lesson walks through it).

Both delete only the signed-in caller: the id comes from the verified
session token, never from the request.
"""
from fastapi import APIRouter, Depends
from supabase_auth.types import User

from app.core.auth import delete_auth_user, get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.delete("/users/me")
async def delete_user(user: User = Depends(get_current_user)) -> dict:
    return await delete_auth_user(user.id)
