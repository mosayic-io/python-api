"""
You can create any API endpoints you need in this file. Mosayic abstracts away the initialization
and boilerplate code into the API's "app" variable below, allowing you to get started with ease.

Later, if you need to more control, you can access the FastAPI app instance directly, or just create your own.
"""
from fastapi import Depends
from supabase_auth.types import User

from app import app
from app.core.auth import get_current_user
from app.routes.auth_router import router as auth_router


@app.get("/")
async def public_route():
    return {"message": "Welcome to the Python API!"}


@app.get("/protected")
async def protected_route(user: User = Depends(get_current_user)):
    return {"message": "You are authenticated!", "user_id": user.id}


app.include_router(auth_router)
