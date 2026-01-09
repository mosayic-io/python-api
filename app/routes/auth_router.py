from fastapi import APIRouter, Depends
from supabase_auth.types import User

from app.core.auth import delete_auth_user, get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, _: User = Depends(get_current_user)) -> dict:
    return await delete_auth_user(user_id)
