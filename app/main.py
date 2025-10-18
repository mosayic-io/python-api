from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.routers.caloratio_router import router as caloratio_router
from app.routers.charm_router import router as charm_router
from app.routers.teamup_router import router as teamup_router
from app.routers.homepage_router import router as homepage_router
from app.routers.notifications_router import router as notifications_router
from app.routers.tags_router import router as tags_router
from app.routers.credits_router import router as credits_router
from app.core.config import get_settings
from app.services.logger import get_logger
from app.core.firebase import initialize_firebase

logger = get_logger(__name__)
settings = get_settings()
DEBUG_MODE = settings.debug_mode


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_firebase()
    logger.info("Application startup: Initializing services...")
    yield


# Set up FastAPI app - docs will be disabled dynamically in production
app = FastAPI(
    title="Poc API",
    lifespan=lifespan,
    generate_unique_id_function=lambda route: route.name,
    docs_url=None if settings.environment == "production" else "/docs",
    redoc_url=None if settings.environment == "production" else "/redoc",
)


# TODO: Set explicit CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_charset_to_json_response(request: Request, call_next):
    """
    This middleware ensures that all JSON responses have the 'charset=utf-8'
    in their 'Content-Type' header. This is crucial for clients that do not
    default to UTF-8, preventing character encoding issues.
    """
    response = await call_next(request)
    if "application/json" in response.headers.get(
        "content-type", ""
    ) and "charset" not in response.headers.get("content-type", ""):
        response.headers["content-type"] = "application/json; charset=utf-8"
    return response


# Include routers
app.include_router(caloratio_router, prefix="/caloratio", tags=["Caloratio"])
app.include_router(charm_router, prefix="/charm", tags=["Charm"])
app.include_router(teamup_router, prefix="/teamup", tags=["Teamup"])
app.include_router(homepage_router, prefix="/homepage", tags=["Homepage"])
app.include_router(tags_router, prefix="/tags", tags=["Tags"])
app.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
app.include_router(credits_router, prefix="/credits", tags=["Credits"])


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Poc API",
        "debug_mode": DEBUG_MODE,
        "environment": settings.environment
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "poc-api",
        "debug": DEBUG_MODE,
        "environment": settings.environment
    }
