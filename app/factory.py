"""
create_app() assembles the whole API: settings, lifespan, CORS, docs and
every router. `app/main.py` calls it once for uvicorn; each test calls it for
a fresh app of its own.

Register a new router in the list below.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import Settings, get_settings
from app.core.supabase_auth_client import SupabaseAuth
from app.routes.auth_router import router as auth_router
from app.routes.demo_router import router as demo_router
from app.routes.email_router import router as email_router

ROUTERS = [demo_router, auth_router, email_router]


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Building SupabaseAuth makes no network call, so startup never waits
        # on Supabase and never fails on a blank SUPABASE_URL.
        app.state.auth = SupabaseAuth.from_settings(settings)
        try:
            yield
        finally:
            await app.state.auth.aclose()

    # Interactive API docs are only exposed outside production
    is_production = settings.app_env == "production"

    app = FastAPI(
        lifespan=lifespan,
        generate_unique_id_function=lambda route: route.name,
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
    )

    # CORS only applies to browser clients (not the mobile app).
    # TODO: If you add a web frontend, replace "*" with its explicit origins.
    # Auth is a Bearer header, never a cookie, so credentials mode stays off.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in ROUTERS:
        app.include_router(router)

    return app
