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
