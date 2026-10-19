from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import get_settings

settings = get_settings()

# Interactive API docs are only exposed outside production
is_production = settings.app_env == "production"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


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
