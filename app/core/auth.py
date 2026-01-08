from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase_auth.types import User

from app.core.supabase_client import SupabaseClient

auth_scheme = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> User:
    """Dependency to verify JWT and return the current user."""
    token = credentials.credentials
    try:
        client = SupabaseClient()
        user_response = await client.verify_token(token)
        return user_response.user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


async def delete_auth_user(user_id: str) -> dict:
    """Delete a user from Supabase Auth by user ID."""
    try:
        client = SupabaseClient()
        supabase = await client.get_client()
        await supabase.auth.admin.delete_user(user_id)
        return {"deleted_user_id": user_id}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {exc}",
        )
