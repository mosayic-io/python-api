"""The two example routes every fresh API ships: one public, one protected."""
from fastapi import APIRouter, Depends
from supabase_auth.types import User

from app.core.auth import get_current_user

router = APIRouter(tags=["Demo"])


@router.get("/")
async def public_route():
    return {"message": "Welcome to the Python API!"}


@router.get("/protected")
async def protected_route(user: User = Depends(get_current_user)):
    return {"message": "You are authenticated!", "user_id": user.id}
